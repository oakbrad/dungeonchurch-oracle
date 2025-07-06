#!/usr/bin/env python3
import boto3
import os
from datetime import datetime
import sys
import tempfile

def download_latest_dump():
    """
    Download the latest PostgreSQL dump file from OCI S3 compatible storage.
    Uses environment variables for configuration:
    - DUNGEONCHURCH_S3_URL: The S3 endpoint URL
    - DUNGEONCHURCH_S3_NAMESPACE: The S3 namespace
    - DUNGEONCHURCH_S3_BUCKET: The S3 bucket name
    - AWS_ACCESS_KEY_ID: The S3 access key
    - AWS_SECRET_ACCESS_KEY: The S3 secret key
    """
    # Get environment variables
    s3_url = os.environ.get('DUNGEONCHURCH_S3_URL')
    namespace = os.environ.get('DUNGEONCHURCH_S3_NAMESPACE')
    bucket = os.environ.get('DUNGEONCHURCH_S3_BUCKET')
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

    if not all([s3_url, namespace, bucket, access_key, secret_key]):
        print("Error: Required environment variables are missing.")
        print("Required: DUNGEONCHURCH_S3_URL, DUNGEONCHURCH_S3_NAMESPACE, DUNGEONCHURCH_S3_BUCKET")
        print("Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

    # Configure S3 client with OCI endpoint and explicit credentials
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    print(f"Connecting to S3 endpoint: {s3_url}")
    print(f"Looking for dump files in bucket: {bucket}")

    try:
        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            print("No objects found in the bucket.")
            sys.exit(1)
        
        # Filter for .dump files and find the most recent one
        dump_files = []
        for obj in response['Contents']:
            if obj['Key'].endswith('.dump'):
                dump_files.append(obj)
        
        if not dump_files:
            print("No .dump files found in the bucket.")
            sys.exit(1)
        
        # Sort by last modified date
        latest_dump = sorted(dump_files, key=lambda x: x['LastModified'])[-1]
        latest_key = latest_dump['Key']
        
        print(f"Found latest dump file: {latest_key}")
        print(f"Last modified: {latest_dump['LastModified']}")
        print(f"Size: {latest_dump['Size']} bytes")
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "latest.dump")
        
        print(f"Downloading to temporary file: {temp_file}")
        
        # Download the file
        s3_client.download_file(bucket, latest_key, temp_file)
        
        print(f"Download complete. File saved to {temp_file}")
        print(f"File size: {os.path.getsize(temp_file)} bytes")
        
        # Clean up
        os.remove(temp_file)
        os.rmdir(temp_dir)
        print("Temporary files cleaned up.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_latest_dump()
