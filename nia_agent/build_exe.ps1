# build_exe.ps1 - Script to package Nia Agent into a single executable

Write-Host "Installing PyInstaller..."
python -m pip install pyinstaller

Write-Host "Building Nia executable..."
python -m PyInstaller --onefile --windowed --icon=nia_avatar.jpg `
  --name "NiaAgent" `
  --add-data "config.example.json;." `
  --add-data "nia_avatar.jpg;." `
  --add-data "nia_bot.html;." `
  --add-data "3d-agent;3d-agent" `
  --add-data "mouth_frames;mouth_frames" `
  --hidden-import PyQt6.QtWebEngineWidgets `
  --hidden-import PyQt6.QtWebEngineCore `
  nia_gui.py

Write-Host "Build complete! Check the 'dist' folder for NiaAgent.exe"

