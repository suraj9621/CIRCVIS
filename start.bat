@echo off
REM CIRCVIS Full Project Launcher (Windows)
REM Installs dependencies, prepares data, trains models if needed, and starts the backend.

setlocal enabledelayedexpansion

cls
echo ========================================================
echo CIRCVIS - Context-Aware Waste Classification
echo ========================================================
echo.

REM Ensure the script runs from the repository root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Find a usable Python interpreter and avoid the WindowsApps stub
set "PYTHON_CMD="+
set "PYTHON_ARGS="

REM If a virtual environment exists, activate it to prefer venv python
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

if exist "venv\Scripts\python.exe" (
    call :CheckPython "venv\Scripts\python.exe" ""
    if defined PYTHON_CMD goto :PythonFound
)

for /f "usebackq delims=" %%i in (`where py 2^>nul`) do (
    call :CheckPython "%%i" "-3.10"
    if defined PYTHON_CMD goto :PythonFound
    call :CheckPython "%%i" "-3.12"
    if defined PYTHON_CMD goto :PythonFound
)

for /f "usebackq delims=" %%i in (`where python 2^>nul`) do (
    call :CheckPython "%%i" ""
    if defined PYTHON_CMD goto :PythonFound
)
for /f "usebackq delims=" %%i in (`where python3 2^>nul`) do (
    call :CheckPython "%%i" ""
    if defined PYTHON_CMD goto :PythonFound
)
REM Final fallback: try plain `python` on PATH
if not defined PYTHON_CMD (
    echo Trying "python" from PATH as fallback...
    call :CheckPython "python" ""
)
echo ERROR: Python 3.10+ with TensorFlow not found.
echo Run fix_env.bat first, then start.bat again.
pause
exit /b 1

:PythonFound
for /f "usebackq tokens=*" %%i in (`"%PYTHON_CMD%" %PYTHON_ARGS% --version 2^>^&1`) do set "PYTHON_VER=%%i"
echo [OK] Python found: %PYTHON_VER%
echo [OK] Command: %PYTHON_CMD% %PYTHON_ARGS%
echo.

goto :ContinueMain

:CheckPython
set "CAND=%~1"
set "ARGS=%~2"
echo %CAND% | findstr /i "WindowsApps" >nul
if not errorlevel 1 goto :eof
"%CAND%" %ARGS% -c "import sys; import tensorflow" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=%CAND%"
    set "PYTHON_ARGS=%ARGS%"
)
goto :eof

:ContinueMain

REM Set Python path for imports
set "PYTHONPATH=%SCRIPT_DIR%"

REM Install dependencies
echo [STEP 1/4] Installing dependencies...
call "%PYTHON_CMD%" %PYTHON_ARGS% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip. Continuing with existing environment.
) else (
    echo [OK] pip upgraded
)

call "%PYTHON_CMD%" %PYTHON_ARGS% -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Failed to install some dependencies from requirements.txt.
    echo Please check the output and install missing packages manually.
) else (
    echo [OK] Dependencies installed
)
echo.

REM Prepare dataset if required
echo [STEP 2/4] Preparing dataset...
if not exist "data\processed\splits" (
    echo  - Organizing RealWaste and TACO datasets...
    call "%PYTHON_CMD%" %PYTHON_ARGS% data\etl.py
    if errorlevel 1 (
        echo [WARNING] ETL pipeline failed. The frontend may still work in demo mode.
    ) else (
        echo [OK] Data prepared
    )
) else (
    echo [OK] Data already prepared
)
echo.

REM Train models if missing
echo [STEP 3/4] Checking trained models...
if exist "models\circvis_model.keras" goto ModelsReady

echo  - Fine-tuning MobileNetV2 model (may take time)...
"%PYTHON_CMD%" %PYTHON_ARGS% data\finetune_model.py --epochs 15
if errorlevel 1 (
    echo [WARNING] Model training failed. The API may start in demo mode.
) else (
    echo [OK] Models trained successfully
)

goto ModelsCheckDone

:ModelsReady
echo [OK] Trained models already available

:ModelsCheckDone
echo.

REM Start backend server
echo [STEP 4/4] Starting CIRCVIS Backend Server...
echo.
set "PORT=8000"
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 8000 busy - using 8001
    set "PORT=8001"
)
echo ========================================================
echo ✓ CIRCVIS Ready!
echo ========================================================
echo.
echo API Base:   http://localhost:%PORT%
echo Landing:   http://localhost:%PORT%/
echo Demo:      http://localhost:%PORT%/demo.html
echo Dashboard: http://localhost:%PORT%/dashboard.html
echo.
echo Press Ctrl+C to stop server
echo.
echo ========================================================
echo.

call "%PYTHON_CMD%" %PYTHON_ARGS% -m uvicorn backend.app.main:app --host 0.0.0.0 --port %PORT%

echo.
echo Server stopped.
pause