"""
Run both backend and frontend servers together.
Automatically kills existing processes before starting.
Usage: python run.py
"""

import subprocess
import sys
import os
import time
import signal

def kill_existing_processes():
    """Kill any existing uvicorn/node processes on our ports."""
    print("[*] Checking for existing processes...")
    
    if sys.platform == 'win32':
        # Kill processes using port 8000 (backend)
        try:
            result = subprocess.run(
                'netstat -ano | findstr :8000',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, 
                                 capture_output=True)
                    print(f"    Killed process on port 8000 (PID {pid})")
        except:
            pass
        
        # Kill processes using port 3000 (frontend)
        try:
            result = subprocess.run(
                'netstat -ano | findstr :3000',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True,
                                 capture_output=True)
                    print(f"    Killed process on port 3000 (PID {pid})")
        except:
            pass
        
        # Also clean up Next.js lock file if exists
        lock_file = os.path.join(os.path.dirname(__file__), 'frontend', '.next', 'dev', 'lock')
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print("    Removed Next.js lock file")
            except:
                pass
    
    print("[*] Ready to start servers\n")


def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(project_root, 'venv', 'Scripts', 'python.exe')
    frontend_dir = os.path.join(project_root, 'frontend')
    
    # Kill existing processes first
    kill_existing_processes()
    
    processes = []
    
    try:
        print("=" * 60)
        print(" Starting Stock Analysis Web Application")
        print("=" * 60)
        
        # Start Backend
        print("\n[1/2] Starting FastAPI Backend on port 8000...")
        backend_process = subprocess.Popen(
            [venv_python, '-m', 'uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000'],
            cwd=project_root,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        processes.append(backend_process)
        time.sleep(2)  # Wait for backend to start
        
        # Start Frontend
        print("[2/2] Starting Next.js Frontend on port 3000...")
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        processes.append(frontend_process)
        
        print("\n" + "=" * 60)
        print(" Both servers are running!")
        print("=" * 60)
        print("\n  Backend:  http://localhost:8000")
        print("  Frontend: http://localhost:3000")
        print("\n  Press Ctrl+C to stop all servers")
        print("=" * 60 + "\n")
        
        # Wait for processes
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"\nProcess exited with code {p.returncode}")
                    raise KeyboardInterrupt
                    
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        for p in processes:
            try:
                if sys.platform == 'win32':
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except:
                pass
        print("All servers stopped.")


if __name__ == "__main__":
    main()
