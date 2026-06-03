#pip install google-cloud-logging pandas
from google.cloud import logging_v2
import pandas as pd
from datetime import datetime, timedelta, timezone
import re


PROJECT_ID = "healix-dev-v1"


def fetch_logs_last_2_days():

    client = logging_v2.Client(project=PROJECT_ID)

    start_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

    query = f'''
    resource.type="aiplatform.googleapis.com/PredictionService"
    timestamp >= "{start_time}"
    '''

    print("Querying logs...\n")

    entries = client.list_entries(
        filter_=query,
        order_by="timestamp desc"
    )

    records = []

    for entry in entries:

        payload = entry.payload

        sa_email = None
        model = None

        # -----------------------------
        # Extract service account
        # -----------------------------
        try:
            sa_email = entry._data.get("protoPayload", {}) \
                .get("authenticationInfo", {}) \
                .get("principalEmail")
        except Exception:
            sa_email = None

        # -----------------------------
        # Extract model info (best effort)
        # -----------------------------
        if isinstance(payload, dict):
            model = (
                payload.get("model")
                or payload.get("modelId")
                or payload.get("endpointId")
            )

        if sa_email:
            records.append({
                "timestamp": entry.timestamp,
                "service_account": sa_email,
                "model": model or "unknown"
            })

    return pd.DataFrame(records)


def analyze(df):

    if df.empty:
        print("No logs found for last 2 days.")
        return

    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # ------------------------------------------------
    # DAILY USAGE PER SERVICE ACCOUNT
    # ------------------------------------------------
    summary = (
        df.groupby(["date", "service_account", "model"])
        .size()
        .reset_index(name="request_count")
        .sort_values(["date", "service_account"], ascending=[False, True])
    )

    print("\n===== SERVICE ACCOUNT USAGE (LAST 2 DAYS) =====\n")
    print(summary.to_string(index=False))

    # Save output
    summary.to_csv("sa_usage_last_2_days.csv", index=False)

    print("\nSaved: sa_usage_last_2_days.csv")


if __name__ == "__main__":
    df = fetch_logs_last_2_days()
    analyze(df)
