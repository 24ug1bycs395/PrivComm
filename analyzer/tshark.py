import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STANDARD_WINDOWS_PATHS = [
    r"C:\Program Files\Wireshark\tshark.exe",
    r"C:\Program Files (x86)\Wireshark\tshark.exe"
]

def find_tshark_path() -> Optional[str]:
    """Find tshark executable path from environment variable, PATH, or standard installation paths."""
    env_path = os.getenv("TSHARK_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    path_in_cmd = shutil.which("tshark")
    if path_in_cmd:
        return path_in_cmd

    for std_path in STANDARD_WINDOWS_PATHS:
        if os.path.isfile(std_path):
            return std_path

    return None

def check_tshark_version() -> Dict[str, Any]:
    """Check if TShark is installed and return its version."""
    tshark_bin = find_tshark_path()
    if not tshark_bin:
        return {"installed": False, "version": None, "path": None}

    try:
        res = subprocess.run([tshark_bin, "-v"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "TShark detected"
            return {"installed": True, "version": first_line, "path": tshark_bin}
    except Exception as e:
        logger.warning(f"Failed to query TShark version: {e}")

    return {"installed": False, "version": None, "path": tshark_bin}

def run_tshark_json(pcap_path: str, display_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Run tshark on a PCAP file and return JSON packet structure."""
    tshark_bin = find_tshark_path()
    if not tshark_bin:
        raise FileNotFoundError("TShark executable not found. Please install Wireshark or set TSHARK_PATH.")

    cmd = [tshark_bin, "-r", pcap_path, "-T", "json", "-c", "500"]
    if display_filter:
        cmd.extend(["-Y", display_filter])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            logger.error(f"TShark error: {res.stderr}")
            return []
        if not res.stdout.strip():
            return []
        return json.loads(res.stdout)
    except Exception as e:
        logger.error(f"Error executing TShark JSON dissection: {e}")
        return []
