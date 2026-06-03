#!/usr/bin/env python3

import re
import sys
import subprocess
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = "healix-dev-v1"  # <-- Update this

VERTEX_AI_ROLE = "roles/aiplatform.user"

SERVICE_ACCOUNT_REGEX = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
)


# ============================================================
# UTILITIES
# ============================================================

def run_command(cmd):
    """
    Execute command and return stdout.
    Raises RuntimeError on failure.
    """

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"\nCommand failed:\n"
            f"{' '.join(cmd)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout.strip()


def ensure_gcloud_installed():
    try:
        run_command(["gcloud", "--version"])
    except Exception:
        raise RuntimeError(
            "\ngcloud CLI is not installed.\n"
            "Install Cloud SDK first."
        )


# ============================================================
# AUTHENTICATION
# ============================================================

def ensure_authenticated():
    """
    Verifies active authentication and valid token.

    If authentication is missing or expired:
      - revokes existing auth
      - launches browser login
      - verifies token again
    """

    authenticated = False

    try:
        account = run_command([
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)"
        ])

        if account:
            run_command([
                "gcloud",
                "auth",
                "print-access-token"
            ])

            print(f"Authenticated as: {account}")
            authenticated = True

    except Exception:
        authenticated = False

    if authenticated:
        return

    print("\nAuthentication missing or expired.")
    print("Opening browser for Google login...\n")

    # Clear stale credentials
    subprocess.run(
        ["gcloud", "auth", "revoke", "--all"],
        capture_output=True
    )

    login = subprocess.run(
        [
            "gcloud",
            "auth",
            "login",
            "--update-adc"
        ]
    )

    if login.returncode != 0:
        raise RuntimeError(
            "\ngcloud auth login failed."
        )

    # Verify login worked
    account = run_command([
        "gcloud",
        "auth",
        "list",
        "--filter=status:ACTIVE",
        "--format=value(account)"
    ])

    run_command([
        "gcloud",
        "auth",
        "print-access-token"
    ])

    print(f"Authenticated as: {account}")


# ============================================================
# SERVICE ACCOUNT VALIDATION
# ============================================================

def validate_service_account_name(sa_name):

    if not SERVICE_ACCOUNT_REGEX.match(sa_name):
        raise ValueError(
            "\nInvalid service account name.\n\n"
            "Requirements:\n"
            "- lowercase letters only\n"
            "- digits allowed\n"
            "- hyphens allowed\n"
            "- 6 to 30 characters\n"
            "- start with letter\n"
            "- end with letter or digit\n\n"
            "Example:\n"
            "vertex-ai-agent"
        )


def get_service_account_email(sa_name):
    return (
        f"{sa_name}@"
        f"{PROJECT_ID}.iam.gserviceaccount.com"
    )


# ============================================================
# SERVICE ACCOUNT OPERATIONS
# ============================================================

def service_account_exists(sa_email):

    try:
        run_command([
            "gcloud",
            "iam",
            "service-accounts",
            "describe",
            sa_email
        ])
        return True

    except Exception:
        return False


def create_service_account(sa_name):

    sa_email = get_service_account_email(sa_name)

    if service_account_exists(sa_email):
        print(
            f"Service account already exists:\n"
            f"{sa_email}"
        )
        return sa_email

    print(
        f"Creating service account:\n"
        f"{sa_email}"
    )

    run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "create",
        sa_name,
        "--project",
        PROJECT_ID,
        "--display-name",
        sa_name
    ])

    print("Service account created.")

    return sa_email


# ============================================================
# IAM ROLE
# ============================================================

def grant_vertex_role(sa_email):

    print(
        f"Granting role {VERTEX_AI_ROLE}"
    )

    run_command([
        "gcloud",
        "projects",
        "add-iam-policy-binding",
        PROJECT_ID,
        "--member",
        f"serviceAccount:{sa_email}",
        "--role",
        VERTEX_AI_ROLE,
        "--quiet"
    ])

    print("Role granted.")


# ============================================================
# KEY CREATION
# ============================================================

def create_key(sa_name, sa_email):

    key_path = Path.cwd() / f"{sa_name}-key.json"

    if key_path.exists():
        raise FileExistsError(
            f"\nKey file already exists:\n"
            f"{key_path}"
        )

    print(
        f"Creating key:\n"
        f"{key_path}"
    )

    run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "keys",
        "create",
        str(key_path),
        "--iam-account",
        sa_email
    ])

    print("Key created successfully.")

    return key_path


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:
        print(
            f"\nUsage:\n"
            f"python {Path(__file__).name} "
            f"<service-account-name>\n"
        )
        sys.exit(1)

    sa_name = sys.argv[1].strip()

    print("\nChecking gcloud installation...")
    ensure_gcloud_installed()

    print("Checking authentication...")
    ensure_authenticated()

    print("Validating service account name...")
    validate_service_account_name(sa_name)

    sa_email = create_service_account(sa_name)

    grant_vertex_role(sa_email)

    key_file = create_key(
        sa_name,
        sa_email
    )

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(f"Project           : {PROJECT_ID}")
    print(f"Service Account   : {sa_email}")
    print(f"Role              : {VERTEX_AI_ROLE}")
    print(f"Key File          : {key_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
