import subprocess
import json


PROJECT_ID = "healix-dev-v1"

VERTEX_AI_ROLES = {
    "roles/aiplatform.user",
    "roles/aiplatform.admin",
    "roles/aiplatform.serviceAgent"
}


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip()


# ------------------------------------------------------------
# GET PROJECT IAM POLICY
# ------------------------------------------------------------
def get_project_iam_policy():

    output = run([
        "gcloud",
        "projects",
        "get-iam-policy",
        PROJECT_ID,
        "--format=json"
    ])

    return json.loads(output)


# ------------------------------------------------------------
# FILTER VERTEX AI SERVICE ACCOUNTS
# ------------------------------------------------------------
def list_vertex_ai_service_accounts():

    policy = get_project_iam_policy()

    vertex_service_accounts = set()

    for binding in policy.get("bindings", []):

        role = binding.get("role")

        if role not in VERTEX_AI_ROLES:
            continue

        members = binding.get("members", [])

        for m in members:
            if m.startswith("serviceAccount:"):
                sa = m.replace("serviceAccount:", "")
                vertex_service_accounts.add(sa)

    return sorted(vertex_service_accounts)


# ------------------------------------------------------------
# OPTIONAL: ENRICH WITH SERVICE ACCOUNT DETAILS
# ------------------------------------------------------------
def describe_service_account(sa_email):

    output = run([
        "gcloud",
        "iam",
        "service-accounts",
        "describe",
        sa_email,
        "--format=json"
    ])

    return json.loads(output)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():

    print("\nFetching Vertex AI-related service accounts...\n")

    sas = list_vertex_ai_service_accounts()

    if not sas:
        print("No service accounts found with Vertex AI roles.")
        return

    for sa in sas:

        info = describe_service_account(sa)

        print("=" * 60)
        print(f"Email       : {sa}")
        print(f"Name        : {info.get('displayName')}")
        print(f"Unique ID   : {info.get('uniqueId')}")
        print(f"Disabled    : {info.get('disabled')}")


if __name__ == "__main__":
    main()
