import os
import subprocess
import sys
import pathlib
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true')
    args = parser.parse_args()
    init()
    if shutil.which("nixGL"):
        command = ['nixGL', 'alacritty',  '--title', 'fuse', '--class', 'fuse', '--print-events', '-e', 'python', str(pathlib.Path(__file__).parent.resolve().joinpath('fuse.py')) ]
        if args.d: command.insert(2, '--hold')
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        check_focus_lost(process)
    else:
        command = ['alacritty',  '--title', 'fuse', '--class', 'fuse', '--print-events', '-e', 'python', str(pathlib.Path(__file__).parent.resolve().joinpath('fuse.py')) ]
        if args.d: command.insert(2, '--hold')
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        check_focus_lost(process)


def check_focus_lost(process):
    try:
        for line in process.stdout:
            if not 'Focused(false)' in line: continue
            process.terminate()
            break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()

def init():
    if os.path.isdir(f"/home/{os.getlogin()}/.config/fuse"): return
    shutil.copytree(os.path.join(os.path.dirname(__file__), "res"), f"/home/{os.getlogin()}/.config/fuse")

if __name__ == "__main__":
    main()
