#!/usr/bin/env python3
"""
FastAPI/Flask server for EmailTriageEnv.
Exposes OpenEnv-compliant REST API.
Deployed on Hugging Face Spaces.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from src.environment import EmailTriageEnv, ActionSchema
from inference import OpenAIClient, run_inference_episode, TASK_GRADER_MAP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state for per-user sessions (simple in-memory store)
# In production, use Redis or persistent DB
_sessions: Dict[str, Dict[str, Any]] = {}

# Initialize OpenAI client (optional - handle errors gracefully)
_llm_client: Optional[OpenAIClient] = None
try:
    _llm_client = OpenAIClient()
    logger.info("✓ OpenAI client initialized")
except ValueError as e:
    # Expected when API key not set - this is OK
    logger.info(f"ℹ OpenAI client not initialized: {e}")
    _llm_client = None
except Exception as e:
    # Unexpected error - log but don't crash
    logger.warning(f"⚠ OpenAI client failed unexpectedly: {e}")
    _llm_client = None


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@app.route("/reset", methods=["POST"])
def reset_env():
    """
    Reset environment and return initial state.
    
    Supports both query params and JSON body:
        task_id: "easy", "medium", or "hard" (default: "easy")
        session_id: Optional session identifier
    
    Returns: Initial state dict
    """
    try:
        data = request.get_json(silent=True) or {}
        task_id = request.args.get("task_id") or data.get("task_id", "easy")
        session_id = request.args.get("session_id") or data.get("session_id") or str(datetime.now(timezone.utc).timestamp())
        
        # Validate task_id
        if task_id not in ["easy", "medium", "hard"]:
            return jsonify({"error": f"Invalid task_id: {task_id}"}), 400
        
        # Create new environment for this session
        env = EmailTriageEnv()
        state = env.reset(task_id)
        
        # Store session + cleanup if too many
        if len(_sessions) > 100:
            oldest_session = next(iter(_sessions))
            del _sessions[oldest_session]
            logger.info(f"Session cleanup: removed {oldest_session}")
        
        _sessions[session_id] = {
            "env": env,
            "task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "steps": 0,
        }
        
        # Log in required format
        logger.info(f"[START] task={task_id} session_id={session_id}")
        
        return jsonify({
            "session_id": session_id,
            "task_id": task_id,
            "state": state,
        }), 200
    
    except Exception as e:
        logger.error(f"[ERROR] /reset failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/step", methods=["POST"])
def step_env():
    """
    Execute one environment step.
    
    Request body:
        {
            "session_id": "...",
            "action": {
                "action_type": "classify|prioritize|reply|escalate|archive",
                "target_category": "...",
                "priority_level": 1-5,
                "reply_draft": "...",
                "escalation_reason": "...",
                "confidence": 0.0-1.0
            }
        }
    
    Returns: (state, reward, done, info) as JSON
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        action = data.get("action")
        
        if not session_id or session_id not in _sessions:
            return jsonify({"error": "Invalid or missing session_id"}), 400
        
        if not action or not isinstance(action, dict):
            return jsonify({"error": "Invalid action"}), 400
        
        if "action_type" not in action:
            return jsonify({"error": "Missing action_type in action"}), 400
        
        # Get environment from session
        session = _sessions[session_id]
        env = session["env"]
        
        # Execute step
        state, reward, done, info = env.step(action)
        
        # Update session
        session["steps"] += 1
        action_type = action.get("action_type", "unknown")
        
        # Log in required format
        logger.info(f"[STEP] session_id={session_id} step={session['steps']} action={action_type} reward={reward:.4f} done={done}")
        
        return jsonify({
            "state": state,
            "reward": reward,
            "done": done,
            "info": info,
        }), 200
    
    except Exception as e:
        logger.error(f"[ERROR] /step failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/episode", methods=["POST"])
def run_episode():
    """
    Run a complete episode (multi-step).
    
    Query params:
        task_id: "easy", "medium", "hard" (default: "easy")
        use_llm: true/false (default: true - use LLM client if available)
    
    Returns: Episode results
    """
    try:
        task_id = request.args.get("task_id", "easy")
        use_llm = request.args.get("use_llm", "true").lower() == "true"
        
        # Run episode with LLM client if available
        env = EmailTriageEnv()
        # IMPORTANT: Use LLM client by default if available (validator-injected credentials)
        client = _llm_client if use_llm else None
        
        results = run_inference_episode(
            env=env,
            task_id=task_id,
            client=client,
            model_name="llm" if use_llm else "mock",
            benchmark_name="email-triage",
        )
        
        return jsonify(results), 200
    
    except Exception as e:
        logger.error(f"[ERROR] /episode failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions."""
    return jsonify({
        "sessions": [
            {
                "session_id": sid,
                "task_id": session["task_id"],
                "steps": session["steps"],
                "created_at": session["created_at"],
            }
            for sid, session in _sessions.items()
        ]
    }), 200


@app.route("/state", methods=["GET"])
def get_state():
    """Get current environment state for a session."""
    try:
        session_id = request.args.get("session_id")
        
        if not session_id or session_id not in _sessions:
            return jsonify({"error": "Invalid or missing session_id"}), 400
        
        env = _sessions[session_id]["env"]
        return jsonify({"state": env.get_state()}), 200
    
    except Exception as e:
        logger.error(f"[ERROR] /state failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """Delete a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"[END] session_id={session_id} cleaned_up=true")
        return jsonify({"status": "deleted"}), 200
    return jsonify({"error": "Session not found"}), 404


@app.route("/", methods=["GET"])
def index():
    """API documentation."""
    return jsonify({
        "name": "EmailTriageEnv API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /reset": "Initialize environment (query: task_id=easy|medium|hard)",
            "POST /step": "Execute one step (body: {session_id, action})",
            "POST /episode": "Run complete episode (query: task_id, use_llm=true|false)",
            "GET /sessions": "List active sessions",
            "DELETE /sessions/<session_id>": "Delete session",
        },
        "example_action": {
            "action_type": "classify",
            "target_category": "sales_inquiry",
            "priority_level": 2,
            "confidence": 0.95,
            "reply_draft": "",
            "escalation_reason": "",
        }
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Only runs when executed directly, not when run with gunicorn
    port = int(os.getenv("PORT", 7860))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting EmailTriageEnv API on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"LLM client available: {_llm_client is not None}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
else:
    # When run with gunicorn
    logger.info(f"EmailTriageEnv API initialized (gunicorn)")
    logger.info(f"LLM client available: {_llm_client is not None}")
