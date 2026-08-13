import argparse
import time
from aeroUtil import tPrint

from pymavlink import mavutil

MAV_CMD_NAV_PAYLOAD_PLACE = 94

LANDED_STATE_UNDEFINED = 0
LANDED_STATE_ON_GROUND = 1
LANDED_STATE_IN_AIR = 2
LANDED_STATE_TAKEOFF = 3
LANDED_STATE_LANDING = 4

STATE_WAITING_FOR_APPROACH = "WAITING_FOR_APPROACH"
STATE_DESCENDING = "DESCENDING"
STATE_LANDED_WAITING = "LANDED_WAITING"
STATE_DONE = "DONE"


def connect(ip: str, port: int):
    connection = f"udpin:{ip}:{port}"
    tPrint(f"Connecting: {connection}")
    master = mavutil.mavlink_connection(connection)
    tPrint("Waiting for heartbeat...")
    master.wait_heartbeat()
    tPrint(f"Heartbeat OK: system={master.target_system} component={master.target_component}")
    return master


# Asking for the stream rate of EXTENDED_SYS_STATE and MISSION_CURRENT
def request_message_interval(master, message_id: int, hz: float):
    interval_us = int(1e6 / hz)
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
        0,
        message_id,
        interval_us,
        0, 0, 0, 0, 0
    )


# Returns the waypoint number with MAV_CMD_NAV_PAYLOAD_PLACE command, or None if not found
# This does download the mission from the ArduPilot instance on the plane
def find_payload_place_seq(master, timeout=10) -> int:
    tPrint("Requesting mission list to auto-detect payload-place item...")
    master.mav.mission_request_list_send(master.target_system, master.target_component)
    msg = master.recv_match(type="MISSION_COUNT", blocking=True, timeout=timeout)
    if msg is None:
        tPrint("No MISSION_COUNT received; skipping auto-detect.")
        return None
 
    count = msg.count
    found_seq = None
    for seq in range(count):
        master.mav.mission_request_int_send(master.target_system, master.target_component, seq)
        item = master.recv_match(type="MISSION_ITEM_INT", blocking=True, timeout=timeout)
        if item is None:
            continue
        if item.command == MAV_CMD_NAV_PAYLOAD_PLACE:
            found_seq = seq
            break
 
    if found_seq is not None:
        tPrint(f"Found NAV_VTOL_PAYLOAD_PLACE at mission seq {found_seq}")
    else:
        tPrint("NAV_VTOL_PAYLOAD_PLACE not found in mission.")
    return found_seq


# Pulse the RC channel mapped to RCx_OPTION=173 (payload place abort) high, then release it back to
# no-override. Simulates flipping a switch on a remote control
def trigger_abort(master, channel: int, hold_seconds: float = 1.0, num_channels: int = 18):
    values = [0] * num_channels
    values[channel - 1] = 2000  # "high" position
 
    tPrint(f"Triggering abort on RC channel {channel} (high)...")
    master.mav.rc_channels_override_send(master.target_system, master.target_component, *values)
 
    time.sleep(hold_seconds)
 
    values[channel - 1] = 0  # release override on this channel
    master.mav.rc_channels_override_send(master.target_system, master.target_component, *values)
    tPrint("RC override released.")


# Sends message to rover to start alignment. Still need to look into how to connect laptop to rover
def trigger_aligner_start():
    tPrint("[STUB] Would signal aligner script to begin approach/alignment.")


# Currently returns just false since I don't have any logic for this yet
def check_latch_status() -> bool:
    return False


# ---- Main ----
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("-s", "--payload-place-seq", type=int, default=None,
                         help="Mission seq of NAV_VTOL_PAYLOAD_PLACE item. Auto-detected if omitted.")
    parser.add_argument("-a", "--abort-rc-channel", type=int, default=9,
                         help="RC channel number mapped to RCx_OPTION=173.")
    parser.add_argument("-t", "--latch-timeout", type=float, default=30.0,
                         help="Seconds to wait for latch confirmation once landed.")
    args = parser.parse_args()
 
    master = connect(args.ip, args.port)
 
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_EXTENDED_SYS_STATE, hz=2)
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_MISSION_CURRENT, hz=2)
 
    payload_place_seq = args.payload_place_seq
    if payload_place_seq is None:
        payload_place_seq = find_payload_place_seq(master)
        if payload_place_seq is None:
            tPrint("Could not determine payload-place seq. Pass --payload-place-seq explicitly. Exiting.")
            return
 
    state = STATE_WAITING_FOR_APPROACH
    landed_wait_start = None
    current_mission_seq = None
    landed_state = LANDED_STATE_UNDEFINED
 
    tPrint(f"Monitoring. Target mission seq: {payload_place_seq}. State: {state}")
 
    while state != STATE_DONE:
        msg = master.recv_match(blocking=True, timeout=5)
        if msg is None:
            continue
 
        msg_type = msg.get_type()
 
        if msg_type == "MISSION_CURRENT":
            current_mission_seq = msg.seq
 
        elif msg_type == "EXTENDED_SYS_STATE":
            landed_state = msg.landed_state
 
        # --- state transitions ---
 
        if state == STATE_WAITING_FOR_APPROACH:
            if current_mission_seq == payload_place_seq:
                tPrint("Reached payload-place waypoint. Descending.")
                trigger_aligner_start()
                state = STATE_DESCENDING
 
        elif state == STATE_DESCENDING:
            if landed_state == LANDED_STATE_ON_GROUND:
                tPrint("Plane has landed and is holding. Watching for latch.")
                landed_wait_start = time.time()
                state = STATE_LANDED_WAITING
 
        elif state == STATE_LANDED_WAITING:
            if check_latch_status():
                tPrint("Latch confirmed by aligner.")
                trigger_abort(master, args.abort_rc_channel)
                state = STATE_DONE
            elif time.time() - landed_wait_start > args.latch_timeout:
                tPrint(f"Latch timeout after {args.latch_timeout}s. Aborting and continuing mission.")
                trigger_abort(master, args.abort_rc_channel)
                state = STATE_DONE
 
    tPrint("Mediator finished.")
 
 
# Making sure prevents main from running if imported into another script
if __name__ == "__main__":
    main()
