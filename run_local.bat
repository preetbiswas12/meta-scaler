@echo off
REM Quick start script for Code Test Generation environment

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Code Test Generation - OpenEnv Environment
echo ============================================================
echo.

if "%1"=="demo" (
    echo Running demo...
    python main.py demo
) else if "%1"=="tasks" (
    echo Listing available tasks...
    python main.py tasks
) else if "%1"=="test" (
    echo Running tests...
    python test_integration.py
) else if "%1"=="inference" (
    echo Running inference on all tasks...
    python inference.py --task all --episodes 1 --steps 3
) else if "%1"=="easy" (
    echo Running easy task...
    python inference.py --task easy --steps 3
) else if "%1"=="medium" (
    echo Running medium task...
    python inference.py --task medium --steps 4
) else if "%1"=="hard" (
    echo Running hard task...
    python inference.py --task hard --steps 5
) else (
    echo Usage: run_local.bat [command]
    echo.
    echo Commands:
    echo   demo           - Run interactive demo
    echo   tasks          - Show all available tasks
    echo   test           - Run integration tests
    echo   inference      - Run all tasks with inference
    echo   easy           - Run easy difficulty task
    echo   medium         - Run medium difficulty task
    echo   hard           - Run hard difficulty task
    echo.
    echo Environment variables (optional):
    echo   API_BASE_URL   - API endpoint (default: https://api.openai.com/v1)
    echo   MODEL_NAME     - Model name (default: gpt-3.5-turbo)
    echo   OPENAI_API_KEY - API key for OpenAI
    echo   HF_TOKEN       - Token for Hugging Face
    echo.
)

endlocal
