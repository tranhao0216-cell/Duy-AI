@echo off
setlocal
cd /d "%~dp0"
rem Prefer Python 3.14 even if another Python version is first on PATH.
py -3.14 -c "import sys; sys.exit(sys.version_info[:2] != (3, 14))" >nul 2>&1
if not errorlevel 1 goto python314
python -c "import sys; sys.exit(not (sys.version_info >= (3, 10)))" >nul 2>&1
if not errorlevel 1 goto pythonpath
py -3 -c "import sys; sys.exit(not (sys.version_info >= (3, 10)))" >nul 2>&1
if not errorlevel 1 goto pythonlauncher
echo Khong tim thay Python 3.10+. Hay cai Python 3.14 64-bit kem Python Launcher.
echo Sau khi cai, dong cua so nay va mo lai run.bat.
goto end
:python314
py -3.14 launcher.py
goto end
:pythonpath
python launcher.py
goto end
:pythonlauncher
py -3 launcher.py
:end
pause
endlocal
