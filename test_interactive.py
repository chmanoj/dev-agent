#!/usr/bin/env python3
"""Test script to automate the interactive CLI workflow."""

import subprocess
import time
import os

# Set environment variables
env = os.environ.copy()
env.update({
    'GEMINI_API_KEY': 'AIzaSyDhnUf2W6_nVjyoKFltXsXnYo9azEiChpA',
    'GEMINI_MODEL_NAME': 'gemini-2.5-flash-lite',
    'GEMINI_EMBEDDING_MODEL': 'gemini-embedding-001',
    'PREFERRED_LLM_PROVIDER': 'gemini',
    'GEMINI_EMBEDDING_DIMENSION': '3072'
})

def run_interactive_session():
    """Run the interactive session with automated inputs."""
    
    # Clean up first
    subprocess.run(['rm', '-rf', 'test-app/.dev_agent'], check=False)
    
    # Start the interactive session
    proc = subprocess.Popen(
        ['uv', 'run', 'dev-agent', 'init', 'test-app'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        bufsize=1
    )
    
    # Wait for initialization to complete
    time.sleep(5)
    
    # Send commands
    commands = [
        "next\n",  # Move to specification phase
        "create a new page with joke and current datetime\n",  # Feature description
        "y\n",  # Approve specification
        "next\n",  # Move to design phase
        "y\n",  # Approve design
        "next\n",  # Move to implementation phase
        "y\n",  # Approve tasks
        "generate --task-id task_1\n",  # Generate code for first task
        "exit\n"
    ]
    
    for cmd in commands:
        print(f"Sending: {cmd.strip()}")
        proc.stdin.write(cmd)
        proc.stdin.flush()
        time.sleep(3)  # Wait between commands
    
    # Wait for completion
    stdout, _ = proc.communicate()
    print("Output:")
    print(stdout)
    
    return proc.returncode

if __name__ == "__main__":
    exit_code = run_interactive_session()
    print(f"Process exited with code: {exit_code}")