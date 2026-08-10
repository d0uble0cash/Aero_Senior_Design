# THIS HASN'T BEEN TESTED YET. STILL PLAYING AROUND WITH

import argparse
import time
 
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
    print(f"Connecting: {connection}")
    master = mavutil.mavlink_connection(connection)
    print("Waiting for heartbeat...")
    master.wait_heartbeat()
    print(f"Heartbeat OK: system={master.target_system} component={master.target_component}")
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
    print("Requesting mission list to auto-detect payload-place item...")
    master.mav.mission_request_list_send(master.target_system, master.target_component)
    msg = master.recv_match(type="MISSION_COUNT", blocking=True, timeout=timeout)
    if msg is None:
        print("No MISSION_COUNT received; skipping auto-detect.")
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
        print(f"Found NAV_VTOL_PAYLOAD_PLACE at mission seq {found_seq}")
    else:
        print("NAV_VTOL_PAYLOAD_PLACE not found in mission.")
    return found_seq


# Pulse the RC channel mapped to RCx_OPTION=173 (payload place abort) high, then release it back to
# no-override. Simulates flipping a switch on a remote control
def trigger_abort(master, channel: int, hold_seconds: float = 1.0, num_channels: int = 8):
    values = [0] * num_channels
    values[channel - 1] = 2000  # "high" position
 
    print(f"Triggering abort on RC channel {channel} (high)...")
    master.mav.rc_channels_override_send(master.target_system, master.target_component, *values)
 
    time.sleep(hold_seconds)
 
    values[channel - 1] = 0  # release override on this channel
    master.mav.rc_channels_override_send(master.target_system, master.target_component, *values)
    print("RC override released.")


# Sends message to rover to start alignment. Still need to look into how to connect laptop to rover
def trigger_aligner_start():
    print("[STUB] Would signal aligner script to begin approach/alignment.")


# Currently returns just false since I don't have any logic for this yet
def check_latch_status() -> bool:
    return False
