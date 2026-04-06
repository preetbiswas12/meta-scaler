#!/usr/bin/env python3
"""
Deploy Email Triage OpenEnv to Hugging Face Spaces
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report status."""
    print(f"\n{'='*70}")
    print(f"[*] {description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {result.returncode}")
        return False
    print(f"\n[OK] {description} completed")
    return True


def main():
    """Main deployment flow."""
    print("\n" + "="*70)
    print("EMAIL TRIAGE OPENENV - HUGGING FACE SPACES DEPLOYMENT")
    print("="*70)
    
    # Step 0: Check git
    print("\n[1/5] Checking Git configuration...")
    result = subprocess.run("git config --global user.email", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("[!] Git user email not configured. Setting up...")
        subprocess.run("git config --global user.email 'dev@example.com'", shell=True)
        subprocess.run("git config --global user.name 'Developer'", shell=True)
    print("[OK] Git configured")
    
    # Step 1: Verify HF token
    print("\n[2/5] Checking Hugging Face token...")
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("\n[!] HF_TOKEN not set in environment.")
        print("\nTo get your token:")
        print("  1. Go to: https://huggingface.co/settings/tokens")
        print("  2. Create a new token (or copy existing)")
        print("  3. Set environment variable:")
        print("     PowerShell: $env:HF_TOKEN='hf_xxxxx'")
        print("     CMD:        set HF_TOKEN=hf_xxxxx")
        print("     Bash:       export HF_TOKEN=hf_xxxxx")
        sys.exit(1)
    
    print(f"[OK] HF_TOKEN found: {hf_token[:20]}...")
    
    # Step 2: Get username from HF
    print("\n[3/5] Authenticating with Hugging Face...")
    try:
        from huggingface_hub import HfApi, login
        login(token=hf_token)
        api = HfApi()
        user_info = api.whoami()
        username = user_info["name"]
        print(f"[OK] Authenticated as: {username}")
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        sys.exit(1)
    
    # Step 3: Create space (if not exists)
    print("\n[4/5] Creating Hugging Face Space...")
    space_name = "email-triage-env"
    space_url = f"https://huggingface.co/spaces/{username}/{space_name}"
    
    try:
        from huggingface_hub import create_repo
        try:
            create_repo(
                repo_id=space_name,
                repo_type="space",
                space_sdk="docker",
                exist_ok=True,
                token=hf_token
            )
            print(f"[OK] Space created/confirmed: {space_url}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"[OK] Space already exists: {space_url}")
            else:
                raise
    except Exception as e:
        print(f"[ERROR] Failed to create space: {e}")
        sys.exit(1)
    
    # Step 4: Add remote and push
    print("\n[5/5] Pushing code to Hugging Face Spaces...")
    
    hf_remote_url = f"https://huggingface.co/spaces/{username}/{space_name}"
    
    # Check if remote exists
    result = subprocess.run("git remote | grep huggingface", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("[*] Remote 'huggingface' exists, updating URL...")
        subprocess.run(f"git remote set-url huggingface {hf_remote_url}", shell=True)
    else:
        print("[*] Adding remote 'huggingface'...")
        subprocess.run(f"git remote add huggingface {hf_remote_url}", shell=True)
    
    # Push to HF
    print("[*] Pushing code to HF Spaces (this may take a minute)...")
    result = subprocess.run("git push huggingface main --force", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Code pushed successfully!")
    else:
        print(f"[ERROR] Git push failed:")
        print(result.stderr)
        sys.exit(1)
    
    # Success!
    print("\n" + "="*70)
    print("DEPLOYMENT COMPLETE!")
    print("="*70)
    print(f"\n[OK] Space URL: {space_url}")
    print("\nNext steps:")
    print(f"  1. Go to: {space_url}")
    print("  2. Wait for Docker build to complete (2-5 minutes)")
    print("  3. Check logs: {space_url}?logs")
    print("  4. Once running, your space is accessible at the URL above")
    print("\nTo verify deployment:")
    print(f"  export HF_SPACE_URL='{space_url}'")
    print("  python validator.py")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
