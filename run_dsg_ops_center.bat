@echo off
cls
echo ==========================================
echo   DSGE Circular Operations Platform
echo ==========================================
echo.

REM Navigate to the folder this BAT file lives in
cd /d "%~dp0"

REM Create virtual environment if missing
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv
)

REM Install dependencies
echo Installing / verifying dependencies...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt

REM Kill anything using port 8501
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM Launch Streamlit
start "" ".venv\Scripts\python.exe" -m streamlit run app.py

timeout /t 5 > nul

REM Open clean browser window (no extensions)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" ^
      --disable-extensions ^
      --user-data-dir="%TEMP%\dsg_clean_profile" ^
      http://localhost:8501
) else (
    start "" http://localhost:8501
)

echo.
echo Platform running...
pause
