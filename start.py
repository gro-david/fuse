import subprocess
import sys
import pathlib
import shutil

def main():
    if shutil.which("nixGL"):
        process = subprocess.Popen(
            ['nixGL', 'alacritty', '--hold', '--title', 'fuse', '--class', 'fuse', '--print-events', '-e', 'python', str(pathlib.Path(__file__).parent.resolve().joinpath('fuse.py')) ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        check_focus_lost(process)
    else:
        process = subprocess.Popen(
            ['alacritty', '--title', 'fuse', '--class', 'fuse', '--print-events', '-e', 'python', str(pathlib.Path(__file__).parent.resolve().joinpath('fuse.py')) ],
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


if __name__ == "__main__":
    main()
