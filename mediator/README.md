# Scripts
## Setting up these scripts
- Run `python -m venv .venv_scripts` with your terminal in the scripts folder (you may need to run `python3` instead of `python`)
- Use the `aEnvScripts` bash alias to activate the virtual enviroment (assuming you have the bash commands from `bash_commands`)
- Do `python - pip install -r requirements.txt` to install required packages for the scripts to run

## Currently testing this flow:
- **mediator.py** script runs alongside Mission Planner
- Mediator detects when plane is on the [MAV_CMD_NAV_PAYLOAD_PLACE](https://ardupilot.org/plane/docs/common-mavlink-mission-command-messages-mav_cmd.html#mav-cmd-nav-payload-place) waypoint and is descending
- Mediator sends to rover to start **Aligner** script to align itself under the plane
- Mediator waits for either the rover to latch on, or it takes too long, and tells
plane to continue to the mission.
### This works in a simulated enviroment!
- Specifically, mediator script is able to read from SITL instance, read from its mission, run
dummy aligner script, and tell plane to continue it's mission after rover timesout.
- This was done using the `QuadRC9LandAbort.param` file (includes RC9 Option 173), and with the
`QuadTest2_payload_place.waypoints` file (mediator needs the PAYLOAD_PLACE waypoint to work
correctly). First, run the quadplane SITL instance using the bash script, then, with Mission planner
write the QuadTest2 mission, then run the mediator script with the bash script. Mediator script will
look for the PAYLOAD_PLACE waypoint, and will wait for the plane to reach that waypoint.
- That being said, still need to:
    - [ ] Figure out how to connect Raspberry Pi (maybe with wifi or telemetry as well)
    - [ ] Test this using actual parts instead of a simulated enviroment
