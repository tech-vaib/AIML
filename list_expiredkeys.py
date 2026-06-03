import subprocess
import json
from datetime import datetime, timezone


PROJECT_ID = "healix-dev-v1"


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def get_service_accounts():
    """
    Returns all service accounts in project
    """
    output = run([
        "gcloud",
        "iam",
        "service-accounts",
        "list",
        "--project",
        PROJECT_ID,
        "--format=json"
    ])
    return json.loads(output)


def get_keys(sa_email):
    """
    Returns keys for a service account
    """
    output = run([
        "gcloud",
        "iam",
        "service-accounts",
        "keys",
        "list",
        "--iam-account",
        sa_email,
        "--format=json"
    ])
    return json.loads(output)


def is_expired(key):
    """
    Checks if key is expired based on validBeforeTime
    """
    valid_before = key.get("validBeforeTime")

    # If no expiration, it's a system-managed key (rare)
    if not valid_before:
        return False

    exp_time = datetime.fromisoformat(
        valid_before.replace("Z", "+00:00")
    )

    return exp_time < datetime.now(timezone.utc)


def main():
    expired_keys_report = []

    service_accounts = get_service_accounts()

    for sa in service_accounts:
        sa_email = sa["email"]

        try:
            keys = get_keys(sa_email)
        except Exception:
            continue

        for key in keys:
            if is_expired(key):
                expired_keys_report.append({
                    "service_account": sa_email,
                    "key_id": key.get("name"),
                    "valid_before": key.get("validBeforeTime"),
                    "key_type": key.get("keyType")
                })

    print("\n=== EXPIRED SERVICE ACCOUNT KEYS ===\n")

    if not expired_keys_report:
        print("No expired keys found.")
        return

    for item in expired_keys_report:
        print(f"Service Account : {item['service_account']}")
        print(f"Key ID         : {item['key_id']}")
        print(f"Expired At     : {item['valid_before']}")
        print(f"Key Type       : {item['key_type']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
