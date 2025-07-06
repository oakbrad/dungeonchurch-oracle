#!/usr/bin/env python3
import boto3
import os
from datetime import datetime
import sys
import tempfile
import requests
from urllib.parse import urlparse

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
        # Parse the base URL from the PAR URL
        parsed_url = urlparse(s3_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        # List objects in the bucket using the pre-authenticated request URL
        list_url = f"{s3_url}"
        print(f"Listing objects from: {list_url}")
        
        response = requests.get(list_url)
        if response.status_code != 200:
            print(f"Error listing objects: {response.status_code} - {response.text}")
            sys.exit(1)
            
        # Parse the XML response to find .dump files
        # This is a simplified approach - in production you might want to use xml parsing
        content = response.text
        dump_files = []
        
        # Simple parsing to find .dump files and their last modified dates
        # In a real implementation, you would use proper XML parsing
        lines = content.split('\n')
        current_key = None
        current_modified = None
        
        for line in lines:
            if '<Key>' in line and '</Key>' in line:
                current_key = line.split('<Key>')[1].split('</Key>')[0]
            elif '<LastModified>' in line and '</LastModified>' in line:
                current_modified = line.split('<LastModified>')[1].split('</LastModified>')[0]
                
                if current_key and current_key.endswith('.dump'):
                    dump_files.append({
                        'Key': current_key,
                        'LastModified': current_modified
                    })
                current_key = None
                current_modified = None
        
        if not dump_files:
            print("No .dump files found in the bucket.")
            sys.exit(1)
        
        # Sort by last modified date
        latest_dump = sorted(dump_files, key=lambda x: x['LastModified'])[-1]
        latest_key = latest_dump['Key']
        
        print(f"Found latest dump file: {latest_key}")
        print(f"Last modified: {latest_dump['LastModified']}")
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "latest.dump")
        
        print(f"Downloading to temporary file: {temp_file}")
        
        # Download the file using the pre-authenticated request
        download_url = f"{s3_url}/{latest_key}"
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
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    download_latest_dump()

