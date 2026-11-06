@echo off
setlocal
set "LEO_DIR=%~dp0"
set "LEO_PYTHON=%LEO_DIR%venv\Scripts\python.exe"

if not exist "%LEO_PYTHON%" (
    echo Leo setup is incomplete: "%LEO_PYTHON%" was not found.
    echo Create the environment with: python -m venv "%LEO_DIR%venv"
    echo Then install dependencies with: "%LEO_PYTHON%" -m pip install -r "%LEO_DIR%requirements.txt"
    exit /b 1
)

"%LEO_PYTHON%" -c "import langchain_core, langchain_ollama, langgraph" >nul 2>&1
if errorlevel 1 (
    echo Leo dependencies are missing from the project virtual environment.
    echo Install them with: "%LEO_PYTHON%" -m pip install -r "%LEO_DIR%requirements.txt"
    exit /b 1
)

cd /d "%LEO_DIR%"
"%LEO_PYTHON%" -m core.ui
endlocal
