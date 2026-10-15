"""Run all RabbitMQ consumers in parallel processes."""

import subprocess
import sys
import time

QUEUES = ["inventory", "payments", "notifications", "orchestrator", "audit"]

processes = []

print("Starting consumers...")
for queue in QUEUES:
    cmd = [sys.executable, "scripts/consumer.py", queue]
    proc = subprocess.Popen(cmd)
    processes.append((queue, proc))
    print(f"  - {queue}: PID {proc.pid}")

print("\nAll consumers started. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
        # Check if any process died
        for queue, proc in processes:
            if proc.poll() is not None:
                print(f"Process {queue} died with code {proc.returncode}")
                # Restart it
                cmd = [sys.executable, "scripts/consumer.py", queue]
                new_proc = subprocess.Popen(cmd)
                processes[processes.index((queue, proc))] = (queue, new_proc)
                print(f"Restarted {queue}: PID {new_proc.pid}")
except KeyboardInterrupt:
    print("\nStopping consumers...")
    for queue, proc in processes:
        proc.terminate()
        print(f"  - {queue}: terminated")
    print("Done.")
