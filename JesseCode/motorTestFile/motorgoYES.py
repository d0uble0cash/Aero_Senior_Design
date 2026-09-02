import time
import keyboard
from pymavlink import mavutil

# --- CONFIGURATION ---
CONNECTION_STRING = 'COM4'
BAUD_RATE = 9600

# PWM values for brushed motor ESCs
PWM_NEUTRAL = 1500
PWM_FORWARD = 1800 # Adjust up to 2000 for max speed
PWM_REVERSE = 1200 # Adjust down to 1000 for max speed

def connect_to_fc():
    print(f"Connecting to Flight Controller on {CONNECTION_STRING}...")
    master = mavutil.mavlink_connection(CONNECTION_STRING, baud=BAUD_RATE)
    master.wait_heartbeat()
    print("Heartbeat received! Connection successful.")
    return master

def arm_vehicle(master):
    print("Arming vehicle...")
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
        1, 0, 0, 0, 0, 0, 0
    )
    # Wait a moment for arming sequence to complete
    time.sleep(2)

def disarm_vehicle(master):
    print("Disarming vehicle...")
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
        0, 0, 0, 0, 0, 0, 0
    )

def set_rc_channels(master, ch1, ch2, ch3):
    # Sends PWM overrides to the flight controller. 
    # 65535 means "release control / ignore this channel"
    master.mav.rc_channels_override_send(
        master.target_system, master.target_component,
        ch1,      # Channel 1 (Motor 1)
        ch2,      # Channel 2 (Motor 2)
        ch3,    # Channel 3 (Motor 3)
        65535,    # Channel 4 
        65535,    # Channel 5 
        65535,    # Channel 6 
        65535,    # Channel 7 
        65535     # Channel 8 
    )

def main():
    master = connect_to_fc()
    arm_vehicle(master)

    print("\n--- MOTOR CONTROL ACTIVE ---")
    print("Motor 1 & 3 (Forward/Reverse): Press 'W' for Forward, 'S' for Reverse")
    print("Motor 2 (Turn Left/Right): Press 'Up Arrow' for Forward, 'Down Arrow' for Reverse")
    print("Press 'Q' to stop motors, disarm, and exit.\n")

    try:
        # Control loop runs at ~20Hz to keep overrides active
        while True:
            # Default to neutral (stopped) every loop
            pwm1 = PWM_NEUTRAL
            pwm2 = PWM_NEUTRAL
            pwm3 = PWM_NEUTRAL  

            # Emergency stop and exit
            if keyboard.is_pressed('q'):
                print("Exiting...")
                break
            
            # --- Motor 1 Logic ---
            if keyboard.is_pressed('w'):
                pwm1 = PWM_FORWARD
                pwm3 = PWM_FORWARD
            elif keyboard.is_pressed('s'):
                pwm1 = PWM_REVERSE
                pwm3 = PWM_REVERSE
                
            # --- Motor 2 Logic ---
            if keyboard.is_pressed('up'):
                pwm2 = PWM_FORWARD
            elif keyboard.is_pressed('down'):
                pwm2 = PWM_REVERSE

            # Send the commands to the FC
            set_rc_channels(master, pwm1, pwm2, pwm3)
            
            # Sleep to maintain loop rate (20Hz)
            # Flight controllers will time out if overrides aren't sent continuously
            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected.")
    
    finally:
        # Safety routine: Stop motors, clear overrides, and disarm
        print("Stopping motors...")
        set_rc_channels(master, PWM_NEUTRAL, PWM_NEUTRAL, PWM_NEUTRAL)
        time.sleep(0.1)
        
        # Release RC overrides by sending 0 to all channels
        master.mav.rc_channels_override_send(
            master.target_system, master.target_component,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        
        disarm_vehicle(master)
        print("Safe shutdown complete.")

if __name__ == "__main__":
    main()