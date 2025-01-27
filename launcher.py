import os
import subprocess
import json
import threading
import time
from pathlib import Path
import system
import logging

# Setup logging
logging.basicConfig(filename='/tmp/launcher_error.log', level=logging.ERROR, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Globals to track mode and system info
current_mode = "normal"
username = os.getlogin()
launcher_config = f"/home/{username}/.config/launcher.json"

# Function to get system info
def get_system_info():
    while True:
        try:
            time_now = time.strftime("%Y-%m-%d %H:%M:%S")
            brightness = system.get_brightness()
            volume = system.get_volume()
            percentage, plugged, remaining = system.get_battery_state()
            remaining = f"󱧥 {time.strftime('%H:%M:%S', time.gmtime(remaining))}" if not remaining == -2 else ''
            charging = '󰚥' if plugged else '󰚦'
            keyboard_layout = system.get_keyboard()
            #keyboard_layout = subprocess.getoutput("setxkbmap -query | grep layout | awk '{print $2}'")

            top_bar = f"󰥔 {time_now} | 󰃟 {brightness}% | 󰌌 {keyboard_layout} |  {volume}% | 󱐋 {percentage}% {remaining} {charging} "
            with open("/tmp/launcher_top_bar", "w") as f:
                f.write(top_bar)

            time.sleep(0.5)
        except Exception as e:
            logging.error(f"Error in get_system_info: {e}")

def run_fzf(options):
    try:
        fzf_command = (
          "fzf --header-lines=0 --no-info "
          "--preview "while true; do echo \"$(cat /tmp/launcher_top_bar)\"; sleep 0.5; done" "
          "--preview-window=up:1:follow:wrap:noinfo"
        )
        if 'fish' in os.environ('SHELL'):
          fzf_command = (
              "fzf --header-lines=0 --no-info "
              "--preview 'bash while true; echo \"$(cat /tmp/launcher_top_bar)\"; sleep 0.5; end' "
              "--preview-window=up:1:follow:wrap:noinfo"
          )
        fzf_input = "\n".join(options)
        result = subprocess.run(fzf_command, input=fzf_input, text=True, shell=True, stdout=subprocess.PIPE)
        return result.stdout.strip()
    except Exception as e:
        logging.error(f"Error in run_fzf: {e}")
        return ""

def normal_mode():
    try:
        desktop_dirs = [
            "/run/current-system/sw-share/applications"
        ]
        desktop_files = [
            str(file) for dir_ in desktop_dirs for file in Path(dir_).glob("*.desktop") if file.is_file()
        ]

        options = []
        exec_map = {}

        for desktop_file in desktop_files:
            with open(desktop_file) as f:
                lines = f.readlines()
            name = next((line.split("=", 1)[1].strip() for line in lines if line.startswith("Name=")), "Unknown")
            exec_cmd = next((line.split("=", 1)[1].strip() for line in lines if line.startswith("Exec=")), "")

            # Handle placeholders in the Exec command
            exec_cmd = exec_cmd.replace("%u", "").replace("%U", "").replace("%f", "").replace("%F", "").strip()
            exec_cmd = exec_cmd.replace("@@u", "").replace("@@", "").strip()

            # Handle Flatpak apps
            if "flatpak run" in exec_cmd and not exec_cmd.startswith("/usr/bin/flatpak"):
                app_id = exec_cmd.split("flatpak run", 1)[-1].strip()
                exec_cmd = f"flatpak run {app_id}"

            if name and exec_cmd:
                options.append(name)
                exec_map[name] = exec_cmd

        options.extend([":w", ":d", ":q"])
        selection = run_fzf(options)

        if selection == ":w":
            window_mode()
        elif selection == ":d":
            dashboard_mode()
        elif selection == ":q":
            exit()
        elif selection in exec_map:
            process = subprocess.Popen(exec_map[selection], shell=True, start_new_session=True)
            print(env)
            exit()
    except Exception as e:
        logging.error(f"Error in normal_mode: {e}")

# Window mode: Focus a window
def window_mode():
    global current_mode
    try:
        current_mode = "window"

        window_data = subprocess.getoutput("niri msg windows")
        windows = window_data.split("\n\n")

        options = []
        window_map = {}

        for window in windows:
            lines = [line.strip() for line in window.split("\n") if line.strip()]
            window_id = next((line.split(" ", 2)[2].strip(":") for line in lines if line.startswith("Window ID")), None)
            title = next((line.split(": ", 1)[1] for line in lines if line.startswith("Title:")), None)
            title = title.replace('"', '')

            if window_id and title:
                options.append(title)
                window_map[title] = window_id

        options.extend([":n", ":d", ":q"])
        selection = run_fzf(options)

        if selection == ":n":
            normal_mode()
        elif selection == ":d":
            dashboard_mode()
        elif selection == ":q":
            exit()
        elif selection in window_map:
            window_id = window_map[selection]
            subprocess.run(f"niri msg action focus-window --id {window_id}", shell=True)
            exit()
    except Exception as e:
        logging.error(f"Error in window_mode: {e}")

# Dashboard mode: Launch configured apps
def dashboard_mode():
    global current_mode
    try:
        current_mode = "dashboard"

        if not Path(launcher_config).exists():
            print(f"Config file not found at {launcher_config}")
            exit()

        with open(launcher_config) as f:
            dashboards = json.load(f)

        options = [d["name"] for d in dashboards]
        exec_map = {d["name"]: d["exec"] for d in dashboards}

        options.extend([":n", ":w", ":q"])
        selection = run_fzf(options)

        if selection == ":n":
            normal_mode()
        elif selection == ":w":
            window_mode()
        elif selection == ":q":
            exit()
        elif selection in exec_map:
            subprocess.run(exec_map[selection], shell=True)
            dashboard_mode()
    except Exception as e:
        logging.error(f"Error in dashboard_mode: {e}")

# Start system info updater thread
try:
    threading.Thread(target=get_system_info, daemon=True).start()
except Exception as e:
    logging.error(f"Error starting system info updater thread: {e}")

# Start in normal mode
try:
    normal_mode()
except Exception as e:
    logging.error(f"Error starting in normal mode: {e}")
