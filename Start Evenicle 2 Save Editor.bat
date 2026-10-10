@echo off
setlocal
cd /d "%~dp0"
if exist "Evenicle-2-Save-Editor.exe" (
  start "" "Evenicle-2-Save-Editor.exe"
  exit /b
)
py -3 -c "import tkinter" >nul 2>nul
if not errorlevel 1 (
  py -3 evenicle2_live_editor.py
  if errorlevel 1 pause
  exit /b
)
python -c "import tkinter" >nul 2>nul
if not errorlevel 1 (
  python evenicle2_live_editor.py
  if errorlevel 1 pause
  exit /b
)
echo Python 3 with Tkinter is required.
echo Download it from https://www.python.org/downloads/windows/
echo During setup, enable "Add python.exe to PATH", then run this file again.
echo Release users should download Evenicle-2-Save-Editor.exe instead.
pause
