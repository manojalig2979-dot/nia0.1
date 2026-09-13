import os
import sys
import subprocess
import shutil

def package_nia():
    print("=" * 65)
    print("       NDTechHub - PACKAGING NIA 1.0 STANDALONE EXECUTABLE")
    print("=" * 65)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.abspath(os.path.join(current_dir, ".."))
    agent_dir = os.path.join(workspace_dir, "nia_agent")
    dist_target_dir = os.path.join(current_dir, "downloads")
    os.makedirs(dist_target_dir, exist_ok=True)
    target_binary = os.path.join(dist_target_dir, "Nia-Setup-1.0.exe")
    
    # 1. First check if a pre-compiled binary exists in nia_agent/dist
    existing_agent_binary = os.path.join(agent_dir, "dist", "NiaAgent.exe")
    if os.path.exists(existing_agent_binary):
        print(f"[*] Found pre-built executable at: {existing_agent_binary}")
        shutil.copy2(existing_agent_binary, target_binary)
        size_mb = os.path.getsize(target_binary) / (1024 * 1024)
        print(f"[✓] Successfully deployed installer to: {target_binary} ({size_mb:.2f} MB)")
        return

    # 2. If not present, compile from nia_agent
    entry_script = os.path.join(agent_dir, "nia_gui.py")
    if not os.path.exists(entry_script):
        print(f"[!] Error: Agent entry script {entry_script} not found.")
        return

    sep = ";" if sys.platform.startswith("win") else ":"
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=Nia-Setup-1.0",
        f"--add-data={os.path.join(agent_dir, 'config.example.json')}{sep}.",
        f"--add-data={os.path.join(agent_dir, 'nia_bot.html')}{sep}.",
        f"--add-data={os.path.join(agent_dir, 'nia_avatar.jpg')}{sep}.",
        f"--add-data={os.path.join(agent_dir, '3d-agent')}{sep}3d-agent",
        f"--add-data={os.path.join(agent_dir, 'mouth_frames')}{sep}mouth_frames",
        "--hidden-import", "PyQt6.QtWebEngineWidgets",
        "--hidden-import", "PyQt6.QtWebEngineCore",
        entry_script
    ]

    print(f"[*] Invoking PyInstaller build sequence from {agent_dir}...")
    try:
        subprocess.run(cmd, cwd=agent_dir, check=True)
        built_binary = os.path.join(agent_dir, "dist", "Nia-Setup-1.0.exe")
        if os.path.exists(built_binary):
            shutil.copy2(built_binary, target_binary)
            size_mb = os.path.getsize(target_binary) / (1024 * 1024)
            print(f"[✓] Deployment binary ready: {target_binary} ({size_mb:.2f} MB)")
        else:
            print(f"[!] Warning: Built binary not found at {built_binary}")
    except Exception as e:
        print(f"[X] Packaging pipeline error: {e}")

if __name__ == "__main__":
    package_nia()