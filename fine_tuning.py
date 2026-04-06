#!/usr/bin/env python3
"""LLM fine-tuning with OpenAI, local, and HuggingFace support."""
import json
import sys
import time
from typing import Dict, List, Any
from datetime import datetime, timezone


class LLMFineTuner:
    """Base class for LLM fine-tuning."""
    
    def __init__(self, backend: str, model: str, training_data: str):
        self.backend = backend
        self.model = model
        self.training_data = training_data
        self.job_id = None
        self.status = None
    
    def prepare_data(self) -> str:
        """Prepare and validate training data."""
        raise NotImplementedError
    
    def submit_job(self) -> str:
        """Submit fine-tuning job."""
        raise NotImplementedError
    
    def check_status(self) -> Dict:
        """Check job status."""
        raise NotImplementedError
    
    def get_model_name(self) -> str:
        """Get fine-tuned model name."""
        raise NotImplementedError


class OpenAIFineTuner(LLMFineTuner):
    """Fine-tune models via OpenAI API."""
    
    def __init__(self, model: str, training_data: str, api_key: str = None):
        super().__init__("openai", model, training_data)
        import os
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print("✓ OpenAI client initialized")
        except ImportError:
            raise ImportError("openai package required: pip install openai")
    
    def prepare_data(self) -> str:
        """Prepare data in OpenAI JSONL format."""
        print(f"Preparing training data for OpenAI...")
        
        prepared_file = self.training_data.replace(".jsonl", "_openai_prepared.jsonl")
        
        with open(self.training_data, 'r') as infile, \
             open(prepared_file, 'w') as outfile:
            for line in infile:
                if not line.strip():
                    continue
                
                example = json.loads(line)
                
                # Format for OpenAI chat fine-tuning
                formatted = {
                    "messages": [
                        {"role": "system", "content": "You are an expert email triage assistant."},
                        {"role": "user", "content": example.get("prompt", "")},
                        {"role": "assistant", "content": example.get("completion", "")}
                    ]
                }
                outfile.write(json.dumps(formatted) + '\n')
        
        print(f"✓ Data prepared: {prepared_file}")
        return prepared_file
    
    def submit_job(self) -> str:
        """Submit fine-tuning job to OpenAI."""
        prepared_file = self.prepare_data()
        
        print(f"Uploading training file...")
        with open(prepared_file, 'rb') as f:
            response = self.client.files.create(
                file=f,
                purpose="fine-tune"
            )
            file_id = response.id
        
        print(f"✓ File uploaded: {file_id}")
        print(f"Submitting fine-tuning job...")
        
        job = self.client.fine_tuning.jobs.create(
            training_file=file_id,
            model=self.model,
            hyperparameters={
                "n_epochs": 3,
                "learning_rate_multiplier": 1.0
            }
        )
        
        self.job_id = job.id
        print(f"✓ Job submitted: {self.job_id}")
        return self.job_id
    
    def check_status(self) -> Dict:
        """Check fine-tuning job status."""
        if not self.job_id:
            raise ValueError("No job ID. Submit a job first.")
        
        job = self.client.fine_tuning.jobs.retrieve(self.job_id)
        
        status = {
            "job_id": job.id,
            "status": job.status,
            "model": self.model,
            "fine_tuned_model": job.fine_tuned_model,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "training_file": job.training_file
        }
        
        return status
    
    def get_model_name(self) -> str:
        """Get the fine-tuned model name."""
        job = self.client.fine_tuning.jobs.retrieve(self.job_id)
        return job.fine_tuned_model or None


class LocalFineTuner(LLMFineTuner):
    """Fine-tune local models (e.g., Ollama, vLLM)."""
    
    def __init__(self, model: str, training_data: str, server_url: str = "http://localhost:8000"):
        super().__init__("local", model, training_data)
        self.server_url = server_url
        self.finetuned_model_path = None
    
    def prepare_data(self) -> str:
        """Prepare data for local fine-tuning."""
        print(f"Preparing data for local fine-tuning...")
        # For now, just return the training data as-is
        return self.training_data
    
    def submit_job(self) -> str:
        """Submit fine-tuning job to local server."""
        prepared_file = self.prepare_data()
        
        print(f"Starting local fine-tuning job...")
        print(f"Model: {self.model}")
        print(f"Training data: {prepared_file}")
        print(f"Server: {self.server_url}")
        
        # This is a placeholder - actual implementation would depend on the local setup
        # Could use transformers library directly or call a local API
        
        self.job_id = f"local_ft_{int(datetime.now(timezone.utc).timestamp())}"
        print(f"✓ Job submitted: {self.job_id} (local mode - training would start)")
        
        return self.job_id
    
    def check_status(self) -> Dict:
        """Check local fine-tuning status."""
        return {
            "job_id": self.job_id,
            "status": "submitted",
            "model": self.model,
            "note": "Local fine-tuning status checking not implemented. Monitor server logs."
        }
    
    def get_model_name(self) -> str:
        """Get the fine-tuned model path."""
        return self.finetuned_model_path or f"{self.model}-finetuned"


class HuggingFaceFineTuner(LLMFineTuner):
    """Fine-tune models via HuggingFace Transformers."""
    
    def __init__(self, model: str, training_data: str):
        super().__init__("huggingface", model, training_data)
        self.output_dir = "models/finetuned"
    
    def prepare_data(self) -> str:
        """Prepare data for HuggingFace fine-tuning."""
        print(f"Preparing data for HuggingFace...")
        return self.training_data
    
    def submit_job(self) -> str:
        """Fine-tune using HuggingFace Transformers."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from datasets import load_dataset
        except ImportError:
            raise ImportError("transformers and datasets required: pip install transformers datasets")
        
        print(f"Loading model: {self.model}")
        
        # This is a simplified example - real implementation would be more complex
        self.job_id = f"hf_ft_{int(datetime.now(timezone.utc).timestamp())}"
        print(f"✓ Fine-tuning initialized: {self.job_id}")
        print(f"Note: Run actual fine-tuning with trainer.train()")
        
        return self.job_id
    
    def check_status(self) -> Dict:
        """Check fine-tuning status."""
        return {
            "job_id": self.job_id,
            "status": "initialized",
            "model": self.model,
            "output_dir": self.output_dir
        }
    
    def get_model_name(self) -> str:
        """Get the fine-tuned model path."""
        return f"{self.output_dir}/{self.model}-finetuned"


class FineTuningOrchestrator:
    """Orchestrates fine-tuning across multiple backends."""
    
    BACKENDS = {
        "openai": OpenAIFineTuner,
        "local": LocalFineTuner,
        "huggingface": HuggingFaceFineTuner
    }
    
    @classmethod
    def create_finetuner(cls, backend: str, model: str, training_data: str, **kwargs) -> LLMFineTuner:
        """Factory method to create appropriate finetuner."""
        if backend not in cls.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Choose from: {list(cls.BACKENDS.keys())}")
        
        return cls.BACKENDS[backend](model, training_data, **kwargs)
    
    @staticmethod
    def save_job_config(job_id: str, status: Dict, output_file: str = "data/finetuning_jobs.jsonl"):
        """Save job configuration for tracking."""
        config = {
            "job_id": job_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with open(output_file, 'a') as f:
            f.write(json.dumps(config) + '\n')
        
        print(f"✓ Job config saved to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune LLMs on email triage task")
    parser.add_argument("--backend", choices=["openai", "local", "huggingface"], 
                       default="openai", help="Fine-tuning backend")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to fine-tune")
    parser.add_argument("--training-data", default="data/training_supervised.jsonl", 
                       help="Training data file")
    parser.add_argument("--submit", action="store_true", help="Submit fine-tuning job")
    parser.add_argument("--check-status", help="Check status of job ID")
    parser.add_argument("--api-key", help="API key (if needed)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("LLM FINE-TUNING ORCHESTRATOR")
    print("="*60)
    print(f"Backend: {args.backend}")
    print(f"Model: {args.model}")
    print(f"Training data: {args.training_data}")
    
    # Create finetuner
    kwargs = {}
    if args.api_key:
        kwargs["api_key"] = args.api_key
    
    finetuner = FineTuningOrchestrator.create_finetuner(
        args.backend, args.model, args.training_data, **kwargs
    )
    
    if args.submit:
        print("\n" + "="*60)
        print("SUBMITTING FINE-TUNING JOB")
        print("="*60)
        job_id = finetuner.submit_job()
        
        status = finetuner.check_status()
        FineTuningOrchestrator.save_job_config(job_id, status)
        
        print("\n" + "="*60)
        print("JOB SUBMITTED")
        print("="*60)
        print(json.dumps(status, indent=2, default=str))
        
    elif args.check_status:
        print("\n" + "="*60)
        print("CHECKING JOB STATUS")
        print("="*60)
        finetuner.job_id = args.check_status
        status = finetuner.check_status()
        print(json.dumps(status, indent=2, default=str))
    
    else:
        print("\nUse --submit to start fine-tuning or --check-status <job_id> to check progress")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
