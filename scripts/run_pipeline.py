#!/usr/bin/env python3
import os
import sys
import argparse
from download_latest_dump import download_latest_dump
from process_relationships import process_relationships
from process_colors import process_colors

def run_pipeline(output_file=None, keep_dump=False, dump_file=None):
    """
    Run the complete data pipeline:
    1. Download the latest database dump (if not provided)
    2. Process the dump to extract relationship data
    3. Process collection colors for visualization
    4. Optionally clean up the dump file
    
    Args:
        output_file (str, optional): Path to the output JSON file. If None, a default path will be used.
        keep_dump (bool): Whether to keep the dump file after processing
        dump_file (str, optional): Path to an existing dump file. If None, a new dump will be downloaded.
        
    Returns:
        bool: True if the pipeline completed successfully, False otherwise
    """
    # Step 1: Download the latest database dump (if not provided)
    if dump_file is None:
        print("Step 1: Downloading the latest database dump")
        dump_file = download_latest_dump()
        if not dump_file:
            print("Pipeline failed: Could not download the latest database dump")
            return False
    else:
        print(f"Step 1: Using provided dump file: {dump_file}")
        if not os.path.exists(dump_file):
            print(f"Pipeline failed: Provided dump file does not exist: {dump_file}")
            return False
    
    # Step 2: Process the dump to extract relationship data
    print("\nStep 2: Processing the dump to extract relationship data")
    output_file = process_relationships(dump_file, output_file)
    if not output_file:
        print("Pipeline failed: Could not process the database dump")
        return False
    
    # Step 3: Process collection colors for visualization
    print("\nStep 3: Processing collection colors for visualization")
    # Get the temporary database name from the dump file
    temp_db_name = f"outline_temp_{os.path.basename(dump_file).split('.')[0]}"
    css_file, js_file = process_colors(temp_db_name)
    if not css_file or not js_file:
        print("Warning: Could not process collection colors")
        # Continue with the pipeline even if color processing fails
    
    # Step 4: Clean up the dump file if not keeping it
    if not keep_dump:
        print("\nStep 4: Cleaning up the dump file")
        try:
            os.remove(dump_file)
            print(f"Dump file removed: {dump_file}")
        except Exception as e:
            print(f"Warning: Could not remove dump file: {str(e)}")
    else:
        print(f"\nDump file kept at: {dump_file}")
    
    print("\nPipeline completed successfully!")
    print(f"Graph data saved to: {output_file}")
    if css_file and js_file:
        print(f"Collection colors saved to: {css_file} and {js_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Run the complete data pipeline for D3 visualization')
    parser.add_argument('--output', '-o', help='Path to the output JSON file')
    parser.add_argument('--keep-dump', '-k', action='store_true', help='Keep the dump file after processing')
    parser.add_argument('--dump-file', '-d', help='Path to an existing dump file')
    
    args = parser.parse_args()
    
    success = run_pipeline(args.output, args.keep_dump, args.dump_file)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
