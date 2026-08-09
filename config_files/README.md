# Configuration Files

Here I have files I have made for running the scripts. Note that this assumes you are on linux and
have set up an Arduino SITL enviroment. Read more about it [here](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html#sitl-simulator-software-in-the-loop)

* **bash_commands**: These are commands to make running different things easier (read comments for
more information). Paste it at the very bottom of your `.bashrc` file or, preferably, at the end of
your `.bash_aliases` file, then run `. .bashrc` in your terminal.

* **Connections1**: Used on mission planner to connect a plane instance and the rover instance.

* **Autolanding.param**: These are the parameters for the regular plane frame for DO_LAND_START
command to work correctly in Mission Planner. This file goes into the `~/.config/ardupilot` folder
(create it if you don't have it already).

* **locations.txt**: Here I have the location of Apollo 11 Model Aircraft Field set up. This file
goes into the `~/.config/ardupilot` folder (create it if you don't have it already). The SITL
enviroment will automatically detect to location and let you use it if you have it here.
    * APOLLO11P: This is for the plane
    * APOLLO11R: This is for the rover
