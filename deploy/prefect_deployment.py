"""
Prefect deployment for Hoyo daily automation.

This script is called using Python from the external Prefect installation.
Example: ~/project/housework/prefect/prefect-env/bin/python
"""
import os
import subprocess

# Import from external Prefect installation
try:
    from prefect import flow
    from prefect.schedules import Cron
except ImportError:
    print("ERROR: This script must be run with Prefect's Python environment")
    print("Run: <prefect_path>/venv/bin/python deploy/prefect_deployment.py")
    exit(1)


def run_command_with_stream(command, cwd, description):
    """Run a command and stream its output in real-time"""
    print(f"Running {description}...")

    process = subprocess.Popen(
        command,
        cwd=cwd,
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
        raise Exception(f"{description} failed with exit code {return_code}")

    print(f"✅ {description} completed successfully!")


@flow(log_prints=True)
def hoyo_daily_flow():
    """Daily flow: authenticate, then run checkin and redeem"""
    # Get the hoyo project root directory (parent of deploy/)
    hoyo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hoyo_bin = os.path.join(hoyo_dir, "bin", "hoyo")

    # Step 1: Run authentication
    run_command_with_stream(
        [hoyo_bin, "auth"],
        hoyo_dir,
        "hoyo auth"
    )

    # Step 2: Run checkin and redeem
    run_command_with_stream(
        [hoyo_bin, "checkin", "redeem"],
        hoyo_dir,
        "hoyo checkin redeem"
    )

    print("✅ Hoyo daily flow completed successfully!")


if __name__ == "__main__":
    # Get the hoyo project root directory (parent of deploy/)
    hoyo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print(f"Deploying from: {hoyo_root}")

    # Deploy daily flow (Every day at 10 AM Pacific)
    hoyo_daily_flow.from_source(
        source=hoyo_root,
        entrypoint="deploy/prefect_deployment.py:hoyo_daily_flow"
    ).deploy(
        name="hoyo-daily-flow",
        work_pool_name="personal-pool",
        schedule=Cron("0 10 * * *", timezone="America/Los_Angeles"),
    )

    print("✅ Deployment registered successfully!")