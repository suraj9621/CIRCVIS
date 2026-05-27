@echo off
REM CIRCVIS Complete Setup and Launch Script (Windows)
setlocal enabledelayedexpansion

cls
echo ========================================================
echo CIRCVIS - Context-Aware Waste Classification
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "PYTHONPATH=%SCRIPT_DIR%"

set "PYTHON_EXE="
set "PYTHON_ARGS="

REM 1) Project venv (only if TensorFlow works)
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import tensorflow" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=venv\Scripts\python.exe"
        goto :PythonFound
    )
    echo [WARNING] venv broken or missing TensorFlow. Run fix_env.bat to repair.
)

REM 2) py launcher for a supported Python version
where py >nul 2>&1
if not errorlevel 1 (
    py -3.10 -c "import tensorflow" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3.10"
        goto :PythonFound
    )
    py -3.12 -c "import tensorflow" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3.12"
        goto :PythonFound
    )
)

REM 3) Any python on PATH that has TensorFlow
for /f "usebackq delims=" %%i in (`where python 2^>nul`) do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%i" -c "import tensorflow" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%i"
            set "PYTHON_ARGS="
            goto :PythonFound
        )
    )
)

echo.
echo [ERROR] Koi Python nahi mila jisme TensorFlow installed ho.
echo.
echo Fix:
echo   1. Double-click fix_env.bat  ^(recommended^)
echo   2. Phir dubara run.bat chalao
echo.
pause
exit /b 1

:PythonFound
for /f "tokens=*" %%i in ('"!PYTHON_EXE!" !PYTHON_ARGS! --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Python: %PYTHON_VER%
echo [OK] Command: !PYTHON_EXE! !PYTHON_ARGS!
echo.

echo [STEP 1/4] Installing dependencies...
"!PYTHON_EXE!" !PYTHON_ARGS! -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed. Run fix_env.bat
    pause
    exit /b 1
)
"!PYTHON_EXE!" !PYTHON_ARGS! -c "import tensorflow" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] TensorFlow missing. Run fix_env.bat
    pause
    exit /b 1
)
echo [OK] Dependencies ready
echo.

echo [STEP 2/4] Preparing dataset...
if not exist "data\processed\splits" (
    "!PYTHON_EXE!" !PYTHON_ARGS! data/etl.py
    if errorlevel 1 echo [WARNING] ETL failed - check datasets
) else (
    echo [OK] Data already prepared
)
"!PYTHON_EXE!" !PYTHON_ARGS! data/fix_paper_class.py
if exist "data\processed\splits\train\Paper_Cardboard" (
    echo [OK] Paper/Cardboard in training data
) else (
    echo [WARNING] Paper missing - run retrain.bat after data/etl.py
)
echo.

echo [STEP 3/4] Fine-tuning model...
if not exist "models\circvis_model.keras" (
    echo Training ^(~15-25 min on CPU^)...
    "!PYTHON_EXE!" !PYTHON_ARGS! data/finetune_model.py --epochs 15
) else if not exist "data\processed\splits\train\Paper_Cardboard" (
    echo [WARNING] Old model without paper training - run retrain.bat for best results
) else (
    echo [OK] Model exists: models\circvis_model.keras
    echo       Paper galat ho to: retrain.bat chalao
)
echo.

echo [STEP 4/4] Starting server...
set "PORT=8000"
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 8000 busy - using 8001
    set "PORT=8001"
)
echo !PORT!> .server_port

echo.
echo ========================================================
echo CIRCVIS Ready!
echo   Demo:      http://127.0.0.1:!PORT!/demo.html
echo   Dashboard: http://127.0.0.1:!PORT!/dashboard.html
echo.
echo IMPORTANT: Ye link browser mein kholo ^(file/folder se mat kholo^)
echo ========================================================
echo.

start "" "http://127.0.0.1:!PORT!/demo.html"
"!PYTHON_EXE!" !PYTHON_ARGS! -m uvicorn backend.app.main:app --host 0.0.0.0 --port !PORT!

echo.
echo Server stopped.
pause
