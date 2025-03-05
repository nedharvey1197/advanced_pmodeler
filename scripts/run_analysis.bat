@echo off
setlocal enabledelayedexpansion

REM Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"

REM Run the Python launcher
python "%SCRIPT_DIR%launch_analysis.py" "%~1"

if errorlevel 1 (
    echo Error running analysis
    exit /b 1
) else (
    echo Analysis completed successfully
    exit /b 0
) 