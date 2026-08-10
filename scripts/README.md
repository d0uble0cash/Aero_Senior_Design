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
