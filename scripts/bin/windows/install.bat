@echo off
setlocal enabledelayedexpansion

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

REM Create virtual environment
echo Creating virtual environment...
python -m venv "%PROJECT_ROOT%\venv"
call "%PROJECT_ROOT%\venv\Scripts\activate.bat"

REM Install dependencies
echo Installing dependencies...
pip install -r "%PROJECT_ROOT%\requirements\base.txt"
pip install -r "%PROJECT_ROOT%\requirements\spreadsheet.txt"
pip install -r "%PROJECT_ROOT%\requirements\visualization.txt"

REM Create output directories
echo Creating output directories...
mkdir "%PROJECT_ROOT%\data\output\analysis" 2>nul
mkdir "%PROJECT_ROOT%\data\output\reports" 2>nul
mkdir "%PROJECT_ROOT%\data\output\charts" 2>nul

REM Set up Excel integration
echo Setting up Excel integration...
python "%PROJECT_ROOT%\src\utils\setup_excel.py"

echo Installation completed successfully!
echo.
echo To use the tool:
echo 1. Open data\templates\scenario_template.xlsx
echo 2. Fill in your scenario data
echo 3. Click "Generate Analysis"
echo 4. Find results in data\output\
echo.
pause 