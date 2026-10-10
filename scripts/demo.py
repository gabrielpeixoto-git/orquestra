#!/usr/bin/env python
"""Demo script for Orquestra."""

import subprocess
import sys
import time


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status.

    Args:
        cmd: Command to run.
        description: Description of the command.

    Returns:
        True if successful, False otherwise.
    """
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, shell=True, check=False)
    return result.returncode == 0


def main() -> int:
    """Run demo setup."""
    print("🚀 Orquestra Demo Setup")

    # Step 1: Up containers
    if not run_command(
        "docker compose --profile lite up -d", "1. Starting infrastructure (db, redis, rabbitmq)..."
    ):
        print("❌ Failed to start containers")
        return 1

    print("⏳ Waiting for services to be ready...")
    time.sleep(10)

    # Step 2: Run migrations
    if not run_command("uv run python manage.py migrate", "2. Running migrations..."):
        print("❌ Failed to run migrations")
        return 1

    # Step 3: Seed demo data
    if not run_command("uv run python manage.py seed_demo", "3. Seeding demo data..."):
        print("❌ Failed to seed demo data")
        return 1

    # Step 4: Start server
    print("\n{'='*60}")
    print("4. Starting development server...")
    print(f"{'=' * 60}")
    print("\n✅ Demo setup complete!")
    print("\n📊 Access the application:")
    print("   - API: http://localhost:8000/api/docs")
    print("   - Dashboard: http://localhost:8000/")
    print("   - Health: http://localhost:8000/health/detailed")
    print("\nPress Ctrl+C to stop the server\n")

    return subprocess.run("uv run python manage.py runserver", shell=True, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
