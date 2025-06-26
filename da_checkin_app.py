import streamlit as st
import boto3
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError

# UI Layout
st.title("DA Workflow Check-In Portal")
da_name = st.text_input("Enter your name:")
workflow = st.selectbox("Select your current workflow:", [
    "Binary Preference", "MIL", "Transcription", "RAI - Sensitive Content", "Other"
])

if st.button("Check In"):
    if not da_name or not workflow:
        st.warning("Please fill out all fields before checking in.")
    else:
        try:
            # AWS S3 Setup
            s3 = boto3.client(
                "s3",
                aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
                region_name="us-east-1"
            )
            bucket_name = st.secrets["aws"]["S3_BUCKET"]
            object_key = "logs/DA_Checkin_Data.csv"

            # Attempt to get existing object
            try:
                response = s3.get_object(Bucket=bucket_name, Key=object_key)
                existing_data = pd.read_csv(response["Body"])
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    existing_data = pd.DataFrame(columns=["DA Name", "Workflow", "Timestamp"])
                else:
                    raise e

            # Append new check-in
            new_entry = {
                "DA Name": da_name,
                "Workflow": workflow,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            updated_data = pd.concat([existing_data, pd.DataFrame([new_entry])], ignore_index=True)

            # Save back to S3
            csv_buffer = updated_data.to_csv(index=False)
            s3.put_object(Bucket=bucket_name, Key=object_key, Body=csv_buffer)

            st.success("Check-in successfully recorded!")

        except Exception as e:
            st.error(f" AWS Error: {e}")
