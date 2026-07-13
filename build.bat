@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=py -3.11"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

%PYTHON% -m PyInstaller --noconfirm --clean --windowed --onedir ^
  --name AnimePersonDesktopPet ^
  --icon "assets\app_icon\app_icon.ico" ^
  --add-data "assets;assets" ^
  --add-data "config;config" ^
  main.py
if errorlevel 1 (
  echo Build failed. Review the messages above.
  exit /b 1
)

if not exist release mkdir release
powershell -NoProfile -Command "Compress-Archive -Path 'dist\AnimePersonDesktopPet\*' -DestinationPath 'release\AnimePersonDesktopPet-Windows-x64.zip' -Force"
if errorlevel 1 exit /b 1
echo Build ready: dist\AnimePersonDesktopPet
echo Archive ready: release\AnimePersonDesktopPet-Windows-x64.zip
