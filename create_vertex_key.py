#!/usr/bin/env python3

import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = "ABCD-dev-v1"
VERTEX_AI_ROLE = "roles/aiplatform.user"

SERVICE_ACCOUNT_REGEX = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
)


# ============================================================
# UTILITIES
# ============================================================

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"\nCommand failed:\n{' '.join(cmd)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout.strip()


def ensure_gcloud_installed():
    run_command(["gcloud", "--version"])


# ============================================================
# AUTH
# ============================================================

def ensure_authenticated():

    try:
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

        if account:
            print(f"Authenticated as: {account}")
            return

    except Exception:
        pass

    print("\nNo valid auth found. Opening browser login...\n")

    subprocess.run(["gcloud", "auth", "revoke", "--all"], capture_output=True)

    subprocess.run([
        "gcloud",
        "auth",
        "login",
        "--update-adc"
    ], check=True)

    run_command([
        "gcloud",
        "auth",
        "print-access-token"
    ])


# ============================================================
# VALIDATION
# ============================================================

def validate_service_account_name(name):
    if not SERVICE_ACCOUNT_REGEX.match(name):
        raise ValueError("Invalid service account name")


def get_sa_email(name):
    return f"{name}@{PROJECT_ID}.iam.gserviceaccount.com"


# ============================================================
# SERVICE ACCOUNT
# ============================================================

def sa_exists(email):
    try:
        run_command([
            "gcloud",
            "iam",
            "service-accounts",
            "describe",
            email
        ])
        return True
    except Exception:
        return False


def create_sa(name):
    email = get_sa_email(name)

    if sa_exists(email):
        print(f"Service account exists: {email}")
        return email

    run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "create",
        name,
        "--project",
        PROJECT_ID,
        "--display-name",
        name
    ])

    return email


# ============================================================
# IAM ROLE
# ============================================================

def grant_role(email):
    run_command([
        "gcloud",
        "projects",
        "add-iam-policy-binding",
        PROJECT_ID,
        "--member",
        f"serviceAccount:{email}",
        "--role",
        VERTEX_AI_ROLE,
        "--quiet"
    ])


# ============================================================
# KEY MANAGEMENT
# ============================================================

def list_keys(email):
    out = run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "keys",
        "list",
        "--iam-account",
        email,
        "--format=json"
    ])
    return json.loads(out)


def is_expired(key):
    exp = key.get("validBeforeTime")
    if not exp:
        return False

    return datetime.fromisoformat(
        exp.replace("Z", "+00:00")
    ) < datetime.now(timezone.utc)


def delete_key(email, key_name):
    run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "keys",
        "delete",
        key_name,
        "--iam-account",
        email,
        "--quiet"
    ])


def create_key(name, email):

    key_path = Path.cwd() / f"{name}-key.json"

    keys = list_keys(email)

    active = []
    expired = []

    for k in keys:
        if is_expired(k):
            expired.append(k)
        else:
            active.append(k)

    # ---- expired keys auto delete
    if expired:
        print("\nExpired keys found → auto deleting")
        for k in expired:
            delete_key(email, k["name"])

    # ---- active keys require confirmation
    if active:
        print("\nActive keys exist:")
        for k in active:
            print(" -", k["name"])

        choice = input("\nReplace active key(s)? (yes/no): ").lower()
        if choice != "yes":
            print("Aborted.")
            sys.exit(0)

        for k in active:
            delete_key(email, k["name"])

    # ---- local file check
    if key_path.exists():
        choice = input(
            f"\nLocal file exists: {key_path}\nOverwrite? (yes/no): "
        ).lower()

        if choice != "yes":
            print("Aborted.")
            sys.exit(0)

        key_path.unlink()

    # ---- create new key
    run_command([
        "gcloud",
        "iam",
        "service-accounts",
        "keys",
        "create",
        str(key_path),
        "--iam-account",
        email
    ])

    return key_path


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:
        print("Usage: python script.py <service-account-name>")
        sys.exit(1)

    name = sys.argv[1].strip()

    ensure_gcloud_installed()
    ensure_authenticated()

    validate_service_account_name(name)

    email = create_sa(name)

    grant_role(email)

    key = create_key(name, email)

    print("\n================ SUCCESS ================")
    print("Service Account:", email)
    print("Key File:", key)
    print("Role:", VERTEX_AI_ROLE)
    print("========================================")


if __name__ == "__main__":
    main()
