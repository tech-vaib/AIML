import subprocess
import json
import re
import sys


PROJECT_ID = "healix-dev-v1"

SA_EMAIL_REGEX = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z0-9.-]+\.iam\.gserviceaccount\.com$"
)


# ---------------------------
# UTIL
# ---------------------------
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


# ---------------------------
# VALIDATION
# ---------------------------
def validate_sa_email(sa_email):
    if not SA_EMAIL_REGEX.match(sa_email):
        raise ValueError(
            "Invalid service account email format."
        )


# ---------------------------
# CHECK SA EXISTS
# ---------------------------
def sa_exists(sa_email):
    try:
        run([
            "gcloud",
            "iam",
            "service-accounts",
            "describe",
            sa_email,
            "--project",
            PROJECT_ID
        ])
        return True
    except Exception:
        return False


# ---------------------------
# LIST IAM ROLES
# ---------------------------
def get_sa_roles(sa_email):
    output = run([
        "gcloud",
        "projects",
        "get-iam-policy",
        PROJECT_ID,
        "--format=json"
    ])

    policy = json.loads(output)

    roles = []

    for binding in policy.get("bindings", []):
        if sa_email in binding.get("members", []):
            roles.append(binding["role"])

    return roles


# ---------------------------
# LIST KEYS
# ---------------------------
def get_sa_keys(sa_email):
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


# ---------------------------
# DELETE KEYS
# ---------------------------
def delete_keys(sa_email, keys):
    for key in keys:
        key_name = key["name"]

        print(f"Deleting key: {key_name}")

        run([
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "delete",
            key_name,
            "--iam-account",
            sa_email,
            "--quiet"
        ])


# ---------------------------
# REMOVE IAM ROLES
# ---------------------------
def remove_roles(sa_email, roles):
    for role in roles:
        print(f"Removing role: {role}")

        run([
            "gcloud",
            "projects",
            "remove-iam-policy-binding",
            PROJECT_ID,
            "--member",
            f"serviceAccount:{sa_email}",
            "--role",
            role,
            "--quiet"
        ])


# ---------------------------
# DELETE SERVICE ACCOUNT
# ---------------------------
def delete_service_account(sa_email):
    print(f"Deleting service account: {sa_email}")

    run([
        "gcloud",
        "iam",
        "service-accounts",
        "delete",
        sa_email,
        "--project",
        PROJECT_ID,
        "--quiet"
    ])


# ---------------------------
# MAIN FLOW
# ---------------------------
def main():

    if len(sys.argv) != 2:
        print("Usage: python delete_sa.py <service-account-email>")
        sys.exit(1)

    sa_email = sys.argv[1].strip()

    print("\nValidating input...")
    validate_sa_email(sa_email)

    print("Checking if service account exists...")
    if not sa_exists(sa_email):
        print("Service account does not exist.")
        return

    print("\nFetching attached IAM roles...")
    roles = get_sa_roles(sa_email)

    print("\nFetching keys...")
    keys = get_sa_keys(sa_email)

    print("\n================ SUMMARY =================")
    print(f"Service Account: {sa_email}")
    print("\nRoles attached:")
    for r in roles:
        print(f"  - {r}")

    print("\nKeys:")
    for k in keys:
        print(f"  - {k.get('name')}")

    print("==========================================\n")

    confirm = input(
        "⚠️ This will DELETE the service account, roles, and keys.\n"
        "Type 'DELETE' to confirm: "
    )

    if confirm != "DELETE":
        print("Aborted by user.")
        return

    print("\nStarting deletion process...\n")

    if keys:
        delete_keys(sa_email, keys)

    if roles:
        remove_roles(sa_email, roles)

    delete_service_account(sa_email)

    print("\n✅ Service account and associated resources deleted successfully.")


if __name__ == "__main__":
    main()
