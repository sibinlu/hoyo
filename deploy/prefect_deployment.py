import os
from prefect import flow
from prefect.schedules import Cron

@flow(log_prints=True)
def hoyo_auth_flow():
    """Weekly authentication renewal flow"""
    import subprocess

    # Path to hoyo project directory
    hoyo_dir = "/Users/sixomac/project/hoyo"

    # Run auth using local binary (can't run in Docker due to browser requirement)
    print("Running hoyo auth locally...")

    # Stream output in real-time
    process = subprocess.Popen(
        ["/Users/sixomac/project/hoyo/bin/hoyo", "auth"],
        cwd=hoyo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Print each line as it comes
    for line in process.stdout:
        print(line.rstrip())

    # Wait for completion and check return code
    return_code = process.wait()
    if return_code != 0:
        raise Exception(f"Command failed with exit code {return_code}")

    print("✅ Hoyo authentication completed successfully!")

@flow(log_prints=True)
def hoyo_checkin_flow():
    """Daily checkin and redeem flow"""
    import subprocess

    # Path to hoyo project directory
    hoyo_dir = "/Users/sixomac/project/hoyo"

    # Check if session file exists at custom SESSION_PATH location
    session_file = "/Users/sixomac/SessionData/hoyo_session_data.json"
    if not os.path.exists(session_file):
        print("⚠️ No authentication session found!")
        print(f"Expected session file at: {session_file}")
        print("Please run: cd /Users/sixomac/project/hoyo && ./bin/hoyo auth")
        raise Exception("Authentication required. Please run './bin/hoyo auth' locally first.")

    # Run checkin and redeem using Docker
    print("Running hoyo checkin and redeem via Docker...")
    print(f"Working directory: {hoyo_dir}")

    # Stream output in real-time
    process = subprocess.Popen(
        ["docker-compose", "run", "--rm", "hoyo", "checkin", "redeem"],
        cwd=hoyo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Print each line as it comes
    for line in process.stdout:
        print(line.rstrip())

    # Wait for completion and check return code
    return_code = process.wait()
    if return_code != 0:
        print(f"❌ Docker command failed with exit code {return_code}")
        raise Exception(f"Docker command failed with exit code {return_code}")

    print("✅ Hoyo checkin completed successfully!")

if __name__ == "__main__":
    # Get the hoyo project root directory (parent of deploy/)
    hoyo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Deploy weekly auth flow (Sundays at 2 AM)
    hoyo_auth_flow.from_source(
        source=hoyo_root,
        entrypoint="deploy/prefect_deployment.py:hoyo_auth_flow"
    ).deploy(
        name="hoyo-auth-weekly",
        work_pool_name="my-local-pool",
        schedule=Cron("0 2 * * 0", timezone="America/Los_Angeles"),  # Sunday 2 AM
    )

    # Deploy daily checkin flow (Every day at 10 AM)
    hoyo_checkin_flow.from_source(
        source=hoyo_root,
        entrypoint="deploy/prefect_deployment.py:hoyo_checkin_flow"
    ).deploy(
        name="hoyo-checkin-daily",
        work_pool_name="my-local-pool",
        schedule=Cron("0 10 * * *", timezone="America/Los_Angeles"),  # Daily 10 AM
    )