#!/usr/bin/env python3
import os
import sys
import tempfile
import requests
import json
from datetime import datetime

def download_latest_dump():
    """
    Download the latest PostgreSQL dump file from OCI S3 compatible storage.
    Uses environment variables for configuration:
    - DUNGEONCHURCH_S3_URL: The pre-authenticated request URL for OCI Object Storage
    - DUNGEONCHURCH_S3_NAMESPACE: The OCI namespace
    - DUNGEONCHURCH_S3_BUCKET: The OCI bucket name
    """
    # Get environment variables
    s3_url = os.environ.get('DUNGEONCHURCH_S3_URL')
    namespace = os.environ.get('DUNGEONCHURCH_S3_NAMESPACE')
    bucket = os.environ.get('DUNGEONCHURCH_S3_BUCKET')

    if not all([s3_url, namespace, bucket]):
        print("Error: Required environment variables are missing.")
        print("Required: DUNGEONCHURCH_S3_URL, DUNGEONCHURCH_S3_NAMESPACE, DUNGEONCHURCH_S3_BUCKET")
        sys.exit(1)

    print(f"Using pre-authenticated request URL: {s3_url}")
    print(f"Namespace: {namespace}")
    print(f"Bucket: {bucket}")

    try:
        # List objects in the bucket using the pre-authenticated request URL
        # The URL already returns a JSON response with the list of objects
        print(f"Listing objects from: {s3_url}")
        
        response = requests.get(s3_url)
        if response.status_code != 200:
            print(f"Error listing objects: {response.status_code} - {response.text}")
            sys.exit(1)
            
        # Parse the JSON response
        try:
            data = response.json()
            
            # Filter for PostgreSQL dump files in the backup folder
            dump_files = []
            for obj in data.get('objects', []):
                name = obj.get('name', '')
                if name.endswith('-outline-postgres.dump') and name.startswith('backup/'):
                    dump_files.append(name)
                    print(f"Found dump file: {name}")
            
            if not dump_files:
                print("No PostgreSQL dump files found with pattern *-outline-postgres.dump")
                sys.exit(1)
            
            # Sort by name (which includes the date in the format YYYY-MM-DD-HH-MM-SS)
            # This works because the date format is sortable as a string
            latest_dump = sorted(dump_files)[-1]
            
            print(f"Found latest dump file: {latest_dump}")
            
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, "latest.dump")
            
            print(f"Downloading to temporary file: {temp_file}")
            
            # Download the file using the pre-authenticated request
            download_url = f"{s3_url}/{latest_dump}"
            print(f"Downloading from: {download_url}")
            
            download_response = requests.get(download_url, stream=True)
            if download_response.status_code != 200:
                print(f"Error downloading file: {download_response.status_code} - {download_response.text}")
                sys.exit(1)
                
            # Save the file
            with open(temp_file, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Download complete. File saved to {temp_file}")
            print(f"File size: {os.path.getsize(temp_file)} bytes")
            
            # Clean up
            os.remove(temp_file)
            os.rmdir(temp_dir)
            print("Temporary files cleaned up.")
            
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response from S3")
            print(f"Response content: {response.text[:200]}...")  # Print first 200 chars for debugging
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_latest_dump()

