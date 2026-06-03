#!/usr/bin/env python3

"""
Creates a GCP service account, grants Vertex AI User role,
and downloads a service account key to the current directory.

Prerequisites:
    - gcloud CLI installed
    - User authenticated:
        gcloud auth login
    - IAM permissions:
        roles/iam.serviceAccountAdmin
        roles/iam.serviceAccountKeyAdmin
        roles/resourcemanager.projectIamAdmin

Usage:
    python create_vertex_service_account.py vertex-ai-agent

Output:
    ./vertex-ai-agent-key.json
"""

import re
import sys
import subprocess
from pathlib import Path


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------

PROJECT_ID = "YOUR_PROJECT_ID"

# Standard Vertex AI User role
VERTEX_AI_ROLE = "roles/aiplatform.user"

# Service account ID validation
# GCP requirements:
# - 6-30 chars
# - lowercase letters, digits, hyphens
# - start with a letter
# - end with letter or digit
SERVICE_ACCOUNT_ID_REGEX = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
)


# ------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------

def run_command(command):
    """
    Execute command and return stdout.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"\nCommand failed:\n"
            f"{' '.join(command)}\n\n"
            f"STDERR:\n{e.stderr}"
        )


def ensure_gcloud_installed():
    """
    Verify gcloud CLI exists.
    """
    try:
        run_command(["gcloud", "--version"])
    except Exception:
        raise RuntimeError(
            "gcloud CLI is not installed or not available in PATH."
        )


def ensure_authenticated():
    """
    Verify active gcloud authentication.
    If not authenticated, attempt login.
    """
    try:
        active_account = run_command(
            [
                "gcloud",
                "auth",
                "list",
                "--filter=status:ACTIVE",
                "--format=value(account)"
            ]
        )

        if active_account:
            print(f"Authenticated as: {active_account}")
            return

    except Exception:
        pass

    print("No active gcloud authentication found.")
    print("Starting gcloud auth login...")

    subprocess.run(
        ["gcloud", "auth", "login"],
        check=True
    )

    active_account = run_command(
        [
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)"
        ]
    )

    if not active_account:
        raise RuntimeError(
            "Authentication failed after login."
        )

    print(f"Authenticated as: {active_account}")


def validate_service_account_id(sa_id):
    """
    Validate service account ID.
    """

    if not SERVICE_ACCOUNT_ID_REGEX.match(sa_id):
        raise ValueError(
            "\nInvalid service account name.\n\n"
            "Requirements:\n"
            "- 6 to 30 characters\n"
            "- lowercase letters, digits, hyphens\n"
            "- must start with a letter\n"
            "- must end with a letter or digit\n\n"
            "Examples:\n"
            "vertex-ai-agent\n"
            "my-ai-service\n"
            "agent-prod01"
        )


# ------------------------------------------------------------------
# SERVICE ACCOUNT OPERATIONS
# ------------------------------------------------------------------

def build_service_account_email(sa_id):
    return f"{sa_id}@{PROJECT_ID}.iam.gserviceaccount.com"


def service_account_exists(sa_email):
    """
    Check whether service account exists.
    """
    try:
        run_command(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "describe",
                sa_email
            ]
        )
        return True

    except Exception:
        return False


def create_service_account(sa_id):
    """
    Create service account if it doesn't exist.
    """
    sa_email = build_service_account_email(sa_id)

    if service_account_exists(sa_email):
        print(
            f"Service account already exists: {sa_email}"
        )
        return sa_email

    print(
        f"Creating service account: {sa_email}"
    )

    run_command(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            sa_id,
            "--project",
            PROJECT_ID,
            "--display-name",
            sa_id
        ]
    )

    print("Service account created.")

    return sa_email


# ------------------------------------------------------------------
# IAM ROLE
# ------------------------------------------------------------------

def grant_vertex_ai_role(sa_email):
    """
    Grant Vertex AI User role.
    """

    print(
        f"Granting {VERTEX_AI_ROLE} to {sa_email}"
    )

    run_command(
        [
            "gcloud",
            "projects",
            "add-iam-policy-binding",
            PROJECT_ID,
            "--member",
            f"serviceAccount:{sa_email}",
            "--role",
            VERTEX_AI_ROLE,
            "--quiet"
        ]
    )

    print("Role granted.")


# ------------------------------------------------------------------
# KEY CREATION
# ------------------------------------------------------------------

def create_key(sa_id, sa_email):
    """
    Create and download key.
    """
    key_path = Path.cwd() / f"{sa_id}-key.json"

    if key_path.exists():
        raise FileExistsError(
            f"\nKey file already exists:\n{key_path}\n\n"
            f"Delete it first or choose another "
            f"service account name."
        )

    print(f"Creating key: {key_path}")

    run_command(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "create",
            str(key_path),
            "--iam-account",
            sa_email
        ]
    )

    print("Key created successfully.")

    return key_path


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def main():

    if PROJECT_ID == "YOUR_PROJECT_ID":
        raise ValueError(
            "Please update PROJECT_ID in the script."
        )

    if len(sys.argv) != 2:
        print(
            f"\nUsage:\n"
            f"python {Path(__file__).name} "
            f"<service-account-name>\n"
        )
        sys.exit(1)

    sa_id = sys.argv[1].strip()

    print("\nValidating input...")
    validate_service_account_id(sa_id)

    print("Checking gcloud installation...")
    ensure_gcloud_installed()

    print("Checking authentication...")
    ensure_authenticated()

    sa_email = create_service_account(sa_id)

    grant_vertex_ai_role(sa_email)

    key_path = create_key(
        sa_id=sa_id,
        sa_email=sa_email
    )

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(f"Project              : {PROJECT_ID}")
    print(f"Service Account      : {sa_email}")
    print(f"Granted Role         : {VERTEX_AI_ROLE}")
    print(f"Key Downloaded To    : {key_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
