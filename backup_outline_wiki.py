#!/usr/bin/env python3
"""
Script to backup Outline wiki data.

This script performs the following steps:
1. Makes an API call to start export of all collections
2. Tracks the progress of the export operation
3. Retrieves the file when it's ready
4. Deletes the backup file on the server
5. Saves the backup file to the repository
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# Get environment variables
OUTLINE_API_TOKEN = os.environ.get('OUTLINE_API_TOKEN')
OUTLINE_URL = os.environ.get('OUTLINE_URL', 'https://app.getoutline.com/api')

# Ensure we have the required environment variables
if not OUTLINE_API_TOKEN:
    print("Error: OUTLINE_API_TOKEN environment variable is required")
    sys.exit(1)

# Setup headers for API requests
headers = {
    'Authorization': f'Bearer {OUTLINE_API_TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def make_api_request(endpoint, data=None):
    """Make a request to the Outline API."""
    url = f"{OUTLINE_URL}/{endpoint}"
    
    # Debug output to see what's being sent
    print(f"Making API request to: {url}")
    print(f"With data: {json.dumps(data or {}, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data or {})
    
    if response.status_code != 200:
        print(f"Error: API request to {endpoint} failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    return response.json()

def start_export():
    """Start the export of all collections."""
    print("Starting export of all collections...")
    # Request JSON format for the export
    response = make_api_request('collections.export_all', {'format': 'json'})
    
    if not response.get('ok'):
        print(f"Error: Failed to start export. Response: {response}")
        sys.exit(1)
    
    file_operation = response.get('data')
    print(f"Export started. File operation ID: {file_operation.get('id')}")
    return file_operation

def track_export_progress(file_operation_id):
    """Track the progress of the export operation."""
    print("Tracking export progress...")
    # Increase max attempts to allow for up to 2 hours (720 attempts * 10 seconds = 2 hours)
    max_attempts = 720
    attempt = 0
    
    while attempt < max_attempts:
        # Debug output to see what's being sent
        print(f"Checking status of file operation: {file_operation_id}")
        
        try:
            # Make the API request with the correct parameter format
            response = make_api_request('fileOperations.info', {'id': file_operation_id})
            
            # Debug output to see the full response
            print(f"Response from fileOperations.info: {json.dumps(response, indent=2)}")
            
            if not response.get('ok'):
                print(f"Error: Failed to get file operation info. Response: {response}")
                sys.exit(1)
            
            file_operation = response.get('data')
            state = file_operation.get('state')
            
            print(f"Export state: {state}")
            
            if state == 'complete':
                print("Export completed successfully!")
                return file_operation
            elif state == 'error':
                print(f"Error: Export failed. Response: {response}")
                sys.exit(1)
            
            attempt += 1
            time.sleep(10)  # Wait for 10 seconds before checking again
        except Exception as e:
            print(f"Error during tracking: {e}")
            print("Retrying in 10 seconds...")
            attempt += 1
            time.sleep(10)
    
    print("Error: Export timed out after 2 hours")
    sys.exit(1)

def download_export(file_operation_id):
    """Download the exported file."""
    print("Getting download URL...")
    response = make_api_request('fileOperations.redirect', {'id': file_operation_id})
    
    if not response.get('ok'):
        print(f"Error: Failed to get download URL. Response: {response}")
        sys.exit(1)
    
    download_url = response.get('data', {}).get('url')
    if not download_url:
        print(f"Error: No download URL found in response. Response: {response}")
        sys.exit(1)
    
    print(f"Downloading file from: {download_url}")
    
    # Download the file
    response = requests.get(download_url)
    if response.status_code != 200:
        print(f"Error: Failed to download file. Status code: {response.status_code}")
        sys.exit(1)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save the file with a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/outline_backup_{timestamp}.zip"
    
    with open(filename, 'wb') as f:
        f.write(response.content)
    
    print(f"File downloaded and saved to: {filename}")
    return filename

def delete_export_from_server(file_operation_id):
    """
    Delete the export file from the server using the fileOperations.delete endpoint.
    """
    print("Attempting to delete the export file from the server...")
    try:
        response = make_api_request('fileOperations.delete', {'id': file_operation_id})
        if response.get('ok'):
            print("Export file deleted from server successfully")
        else:
            print(f"Warning: Failed to delete export file from server. Response: {response}")
    except Exception as e:
        print(f"Warning: Error when trying to delete export file from server: {e}")

def main():
    """Main function to run the backup process."""
    print("Starting Outline wiki backup process...")
    
    # Start the export
    file_operation = start_export()
    file_operation_id = file_operation.get('id')
    
    # Track the progress
    file_operation = track_export_progress(file_operation_id)
    
    # Download the export
    filename = download_export(file_operation_id)
    
    # Try to delete the export from the server
    delete_export_from_server(file_operation_id)
    
    print("Backup process completed successfully!")
    print(f"Backup file saved to: {filename}")
    
    # Create a simple JSON file with metadata about the backup
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'filename': filename,
        'file_operation_id': file_operation_id
    }
    
    with open('data/latest_backup_info.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Backup metadata saved to: data/latest_backup_info.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())

