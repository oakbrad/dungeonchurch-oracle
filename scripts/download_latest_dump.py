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
    
    Returns:
        str: Path to the downloaded dump file, or None if download failed
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
            
            # Create a data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Use a more descriptive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = os.path.join(data_dir, f"outline_postgres_{timestamp}.dump")
            
            print(f"Downloading to file: {dump_file}")
            
            # Download the file using the pre-authenticated request
            # Remove the leading slash to avoid double slashes in the URL
            download_url = f"{s3_url}{latest_dump}"
            print(f"Downloading from: {download_url}")
            
            download_response = requests.get(download_url, stream=True)
            if download_response.status_code != 200:
                print(f"Error downloading file: {download_response.status_code} - {download_response.text}")
                sys.exit(1)
                
            # Save the file
            with open(dump_file, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Download complete. File saved to {dump_file}")
            print(f"File size: {os.path.getsize(dump_file)} bytes")
            
            # Return the path to the downloaded file instead of deleting it
            return dump_file
            
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response from S3")
            print(f"Response content: {response.text[:200]}...")  # Print first 200 chars for debugging
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    dump_file = download_latest_dump()
    if dump_file:
        print(f"Successfully downloaded dump file to: {dump_file}")
        print("You can now process this file with the process_relationships.py script")
    else:
        print("Failed to download dump file")
        sys.exit(1)
