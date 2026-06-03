#pip install google-cloud-logging pandas

from google.cloud import logging_v2
from datetime import datetime, timedelta
import pandas as pd


PROJECT_ID = "ABCD-dev-v1"
SERVICE_ACCOUNT = "kr-test2@healix-dev-v1.iam.gserviceaccount.com"


def fetch_logs():

    client = logging_v2.Client(project=PROJECT_ID)

    query = f'''
    resource.type="aiplatform.googleapis.com/PredictionService"
    protoPayload.authenticationInfo.principalEmail="{SERVICE_ACCOUNT}"
    '''

    entries = client.list_entries(filter_=query, order_by="timestamp desc")

    logs = []

    for entry in entries:

        ts = entry.timestamp
        payload = entry.payload

        model = None
        if isinstance(payload, dict):
            model = payload.get("model") or payload.get("modelId")

        logs.append({
            "timestamp": ts,
            "model": model,
            "service_account": SERVICE_ACCOUNT
        })

    return pd.DataFrame(logs)


def analyze(df):

    if df.empty:
        print("No logs found")
        return

    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    summary = df.groupby(["date", "model"]).size().reset_index(name="calls")

    print("\n===== DAILY LLM USAGE =====\n")
    print(summary.to_string(index=False))

    summary.to_csv("llm_usage_logs.csv", index=False)


if __name__ == "__main__":
    df = fetch_logs()
    analyze(df)
