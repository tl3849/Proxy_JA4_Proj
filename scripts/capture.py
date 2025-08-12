import subprocess
import sys
import os
import time
from datetime import datetime
import argparse
import socket

LOGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOGFILE = os.path.join(LOGDIR, "capture.log")
CAPTURES_DIR = "./captures"

def log(msg):
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def run_cmd(cmd, check=True):
    """Run a command and return stdout, stderr and return code"""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {' '.join(cmd)}")
        log(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e.stdout, e.stderr, e.returncode
    except Exception as e:
        log(f"Exception running command: {e}")
        if check:
            sys.exit(1)
        return "", str(e), -1

def check_container_running(container="capture_poc"):
    """Check if container is running"""
    stdout, stderr, rc = run_cmd(["docker", "ps", "-q", "-f", f"name={container}"], check=False)
    if not stdout.strip():
        log(f"Container {container} is not running! Please start it with 'docker compose up -d'")
        return False
    return True

def list_interfaces():
    if not check_container_running():
        return

    stdout, stderr, rc = run_cmd(
        ["docker", "exec", "capture_poc", "ip", "link"],
        check=False
    )

    if rc == 0:
        interfaces = stdout.replace('\r', ' ').replace('\n', ' ')
        log("Available interfaces in capture_poc: " + interfaces)
    else:
        log("Could not list interfaces in capture_poc.")

def check_tcpdump():
    if not check_container_running():
        return False

    stdout, stderr, rc = run_cmd(
        ["docker", "exec", "capture_poc", "which", "tcpdump"],
        check=False
    )

    if rc != 0:
        log("tcpdump not found in capture_poc container.")
        log("Installing tcpdump...")
        stdout, stderr, rc = run_cmd(
            ["docker", "exec", "capture_poc", "apk", "add", "tcpdump"],
            check=False
        )
        if rc != 0:
            log("Failed to install tcpdump. Error: " + stderr)
            return False
        log("tcpdump installed successfully.")

    stdout, stderr, rc = run_cmd(
        ["docker", "exec", "capture_poc", "tcpdump", "--version"],
        check=False
    )

    if rc == 0:
        version_output = stdout.replace('\r', ' ').replace('\n', ' ')
        log("tcpdump version output: " + version_output)
        return True
    else:
        log("Failed to get tcpdump version. Error: " + stderr)
        return False

def ensure_capture_dir():
    """Ensure capture directory exists"""
    if not os.path.exists(CAPTURES_DIR):
        try:
            os.makedirs(CAPTURES_DIR)
            log(f"Created captures directory: {CAPTURES_DIR}")
        except Exception as e:
            log(f"Error creating captures directory: {e}")
            return False
    return True

def start_tcpdump(interface="any", pcap_name="test.pcap"):
    if not check_container_running() or not check_tcpdump() or not ensure_capture_dir():
        return False

    # Stop any existing tcpdump
    stop_tcpdump(quiet=True)

    # Start tcpdump with timestamp in filename if requested
    if pcap_name == "auto":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pcap_name = f"capture_{timestamp}.pcap"

    container_pcap_path = f"/captures/{pcap_name}"

    stdout, stderr, rc = run_cmd(
        ["docker", "exec", "-d", "capture_poc", "tcpdump", "-i", interface,
         "-w", container_pcap_path, "not", "port", "22"],
        check=False
    )

    if rc != 0:
        log(f"Failed to start tcpdump in capture_poc on interface {interface}. Error: {stderr}")
        return False

    log(f"tcpdump started in capture_poc on interface {interface} -> {container_pcap_path}")

    # Write current capture filename to a file for later reference
    with open(os.path.join(CAPTURES_DIR, ".current_capture"), "w") as f:
        f.write(pcap_name)

    return True

def stop_tcpdump(quiet=False):
    if not check_container_running():
        return False

    stdout, stderr, rc = run_cmd(
        ["docker", "exec", "capture_poc", "pkill", "-INT", "tcpdump"],
        check=False
    )

    if rc != 0 and not quiet:
        log("Failed to send SIGINT to tcpdump in capture_poc (it may not be running)")

    # Give it a moment to finish writing
    time.sleep(2)

    # Try to get current capture filename
    current_capture = "test.pcap"
    current_capture_file = os.path.join(CAPTURES_DIR, ".current_capture")
    if os.path.exists(current_capture_file):
        with open(current_capture_file, "r") as f:
            current_capture = f.read().strip()

    return copy_pcap(current_capture)

def copy_pcap(pcap_name="test.pcap"):
    if not check_container_running() or not ensure_capture_dir():
        return False

    stdout, stderr, rc = run_cmd(
        ["docker", "cp", f"capture_poc:/captures/{pcap_name}", f"{CAPTURES_DIR}/{pcap_name}"],
        check=False
    )

    if rc != 0:
        log(f"Failed to copy {pcap_name} from capture_poc. Error: {stderr}")
        return False

    if os.path.exists(f"{CAPTURES_DIR}/{pcap_name}"):
        size = os.path.getsize(f"{CAPTURES_DIR}/{pcap_name}")
        log(f"{pcap_name} copied to {CAPTURES_DIR} ({size} bytes)")
        return True
    else:
        log(f"{pcap_name} not found in {CAPTURES_DIR}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start or stop packet capture.")
    parser.add_argument("--start", action="store_true", help="Start packet capture")
    parser.add_argument("--stop", action="store_true", help="Stop packet capture")
    parser.add_argument("--interface", type=str, default="eth0", help="Network interface to capture on (default: eth0)")
    parser.add_argument("--output", type=str, default="test.pcap", help="Output pcap filename (use 'auto' for timestamped name)")

    args = parser.parse_args()

    if args.start:
        list_interfaces()
        if start_tcpdump(interface=args.interface, pcap_name=args.output):
            log("Packet capture started successfully.")
        else:
            log("Failed to start packet capture.")
    elif args.stop:
        if stop_tcpdump():
            log("Packet capture stopped and file copied successfully.")
        else:
            log("Failed to stop packet capture or copy file.")
    else:
        log("No action specified. Use --start or --stop.")
        parser.print_help()
