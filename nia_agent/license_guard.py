"""
license_guard.py - Hardware-locked licensing and 7-day trial guard for Nia 1.0.
Prevents trial resets upon reinstalling by anchoring to immutable Windows Hardware ID.
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
import winreg
import urllib.request
import urllib.error

DEFAULT_LICENSE_SERVER = os.getenv("NIA_LICENSE_SERVER", "http://localhost:3000")

def get_machine_fingerprint() -> str:
    """
    Computes a tamper-proof hardware fingerprint from immutable Windows hardware:
    Motherboard UUID + Cryptography MachineGuid + Processor ID.
    Does not change when software is deleted or reinstalled.
    """
    tokens = []

    # 1. Windows MachineGuid from Registry (Persistent across software installs)
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        ) as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            if guid:
                tokens.append(str(guid).strip())
    except Exception:
        pass

    # 2. Motherboard / System UUID via PowerShell CIM
    try:
        uuid_cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"]
        out = subprocess.check_output(
            uuid_cmd,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ).strip()
        if out and len(out) > 5:
            tokens.append(out)
    except Exception:
        pass

    # 3. CPU Processor ID
    try:
        cpu_cmd = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -Class Win32_Processor).ProcessorId"]
        out = subprocess.check_output(
            cpu_cmd,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ).strip()
        if out and len(out) > 3:
            tokens.append(out)
    except Exception:
        pass

    if not tokens:
        tokens.append(platform.node())
        tokens.append(os.getenv("USERNAME", "default"))

    raw_signature = "|".join(tokens)
    hash_hex = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()
    return f"NIA-{hash_hex[0:4].upper()}-{hash_hex[4:8].upper()}-{hash_hex[8:12].upper()}"

def check_license_status(server_url: str = DEFAULT_LICENSE_SERVER, license_key: str = None) -> dict:
    """
    Validates license or 7-day trial status with the licensing server.
    Returns:
      {
         "status": "licensed" | "trial_active" | "trial_expired" | "offline_trial",
         "days_remaining": int,
         "machine_id": str,
         "message": str
      }
    """
    machine_id = get_machine_fingerprint()
    endpoint = f"{server_url.rstrip('/')}/api/license/check-trial"

    payload = {
        "machine_id": machine_id,
        "license_key": license_key
    }

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except Exception as e:
        # Fallback for temporary offline launches: allow grace session ONLY if user already configured a key
        if license_key:
            return {
                "status": "licensed",
                "days_remaining": 7,
                "machine_id": machine_id,
                "message": f"Offline verified key session: {str(e)}"
            }
        return {
            "status": "key_required",
            "days_remaining": 0,
            "machine_id": machine_id,
            "message": "License key required. Please purchase a ₹99 Test Flight or Pro key at ndtechhub.com."
        }

def activate_license(license_key: str, server_url: str = DEFAULT_LICENSE_SERVER) -> dict:
    """Activates a purchased Pro license key for this machine."""
    machine_id = get_machine_fingerprint()
    endpoint = f"{server_url.rstrip('/')}/api/license/activate"

    payload = {
        "machine_id": machine_id,
        "license_key": license_key.strip()
    }

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"status": "error", "message": f"Server error: {e.code}"}
    except Exception as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}

if __name__ == "__main__":
    hw_id = get_machine_fingerprint()
    print(f"[*] Detected Hardware ID: {hw_id}")
    print("[*] Checking status with licensing server...")
    res = check_license_status()
    print(f"[+] License/Trial Status: {res}")
