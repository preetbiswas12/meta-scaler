#!/bin/bash
# Quick start script for Code Test Generation environment

echo ""
echo "============================================================"
echo "Code Test Generation - OpenEnv Environment"
echo "============================================================"
echo ""

case "${1}" in
  demo)
    echo "Running demo..."
    python main.py demo
    ;;
  tasks)
    echo "Listing available tasks..."
    python main.py tasks
    ;;
  test)
    echo "Running tests..."
    python test_integration.py
    ;;
  inference)
    echo "Running inference on all tasks..."
    python inference.py --task all --episodes 1 --steps 3
    ;;
  easy)
    echo "Running easy task..."
    python inference.py --task easy --steps 3
    ;;
  medium)
    echo "Running medium task..."
    python inference.py --task medium --steps 4
    ;;
  hard)
    echo "Running hard task..."
    python inference.py --task hard --steps 5
    ;;
  *)
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  demo           - Run interactive demo"
    echo "  tasks          - Show all available tasks"
    echo "  test           - Run integration tests"
    echo "  inference      - Run all tasks with inference"
    echo "  easy           - Run easy difficulty task"
    echo "  medium         - Run medium difficulty task"
    echo "  hard           - Run hard difficulty task"
    echo ""
    echo "Environment variables (optional):"
    echo "  API_BASE_URL   - API endpoint (default: https://api.openai.com/v1)"
    echo "  MODEL_NAME     - Model name (default: gpt-3.5-turbo)"
    echo "  OPENAI_API_KEY - API key for OpenAI"
    echo "  HF_TOKEN       - Token for Hugging Face"
    echo ""
    ;;
esac
