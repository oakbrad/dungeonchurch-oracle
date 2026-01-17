#!/usr/bin/env python3
import os
import sys
import json
import argparse
from download_latest_dump import download_latest_dump
from process_relationships import process_relationships, restore_database, cleanup_database, get_alignment_collections
from process_colors import process_colors

def run_pipeline(output_file=None, keep_dump=False, dump_file=None):
    """
    Run the complete data pipeline:
    1. Download the latest database dump (if not provided)
    2. Restore the database
    3. Process the dump to extract relationship data
    4. Process collection colors for visualization
    5. Clean up the temporary database
    6. Optionally clean up the dump file
    
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
    
    # Step 2: Restore the database
    print("\nStep 2: Restoring the database")
    db_name = restore_database(dump_file)
    if not db_name:
        print("Pipeline failed: Could not restore the database")
        return False
    
    try:
        # Step 3: Process the dump to extract relationship data
        print("\nStep 3: Processing the dump to extract relationship data")
        # Set default output file if not provided
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        if output_file is None:
            output_file = os.path.join(data_dir, "graph_data.json")
        
        # Extract relationship data
        from process_relationships import extract_relationship_data
        graph_data = extract_relationship_data(db_name)
        if not graph_data:
            print("Failed to extract relationship data")
            return False
        
        # Identify and separate orphaned nodes (nodes with 0 connections)
        print("Identifying orphaned nodes (nodes with 0 connections)")
        orphaned_nodes = [node for node in graph_data['nodes'] if node['connections'] == 0]
        
        # Remove orphaned nodes from the main graph data
        graph_data['nodes'] = [node for node in graph_data['nodes'] if node['connections'] > 0]
        
        # Create orphan data structure
        orphan_data = {
            'nodes': orphaned_nodes,
            'links': []  # No links for orphaned nodes by definition
        }
        
        # Save the main graph data to a JSON file
        print(f"Saving graph data to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        # Save the orphaned nodes to a separate JSON file
        orphan_file = os.path.join(os.path.dirname(output_file), "orphan_data.json")
        print(f"Saving orphaned nodes data to: {orphan_file}")
        with open(orphan_file, 'w') as f:
            json.dump(orphan_data, f, indent=2)
        
        print(f"Graph data saved successfully")
        print(f"Nodes: {len(graph_data['nodes'])}")
        print(f"Links: {len(graph_data['links'])}")
        print(f"Orphaned nodes: {len(orphaned_nodes)}")

        # Step 3.5: Classify alignments for relevant collections
        print("\nStep 3.5: Classifying entity alignments")
        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key:
            from alignment_classifier import classify_alignments

            # Get alignment-eligible collections
            alignment_collections = get_alignment_collections(db_name)

            if alignment_collections:
                # Cache file path
                cache_file = os.path.join(data_dir, "alignment_cache.json")

                # Run classification pipeline
                classify_alignments(
                    nodes=graph_data['nodes'],
                    links=graph_data['links'],
                    alignment_collections=alignment_collections,
                    cache_path=cache_file,
                    api_key=api_key
                )

                # Add alignment collection IDs to graph data for visualization filtering
                graph_data['alignmentCollectionIds'] = list(alignment_collections.values())

                # Re-save graph data with alignment info
                print(f"Re-saving graph data with alignment info to: {output_file}")
                with open(output_file, 'w') as f:
                    json.dump(graph_data, f, indent=2)
            else:
                print("No alignment-eligible collections found, skipping alignment classification")
        else:
            print("OPENAI_API_KEY not set, skipping LLM-based alignment classification")
            # Still run explicit extraction without LLM
            from alignment_classifier import classify_alignments
            alignment_collections = get_alignment_collections(db_name)

            if alignment_collections:
                cache_file = os.path.join(data_dir, "alignment_cache.json")
                classify_alignments(
                    nodes=graph_data['nodes'],
                    links=graph_data['links'],
                    alignment_collections=alignment_collections,
                    cache_path=cache_file,
                    api_key=None  # No LLM, explicit extraction only
                )

                # Add alignment collection IDs to graph data for visualization filtering
                graph_data['alignmentCollectionIds'] = list(alignment_collections.values())

                # Re-save graph data with alignment info
                print(f"Re-saving graph data with alignment info to: {output_file}")
                with open(output_file, 'w') as f:
                    json.dump(graph_data, f, indent=2)

        # Step 4: Process collection colors for visualization
        print("\nStep 4: Processing collection colors for visualization")
        css_file, js_file = process_colors(db_name)
        if not css_file or not js_file:
            print("Warning: Could not process collection colors")
            # Continue with the pipeline even if color processing fails
    
    finally:
        # Step 5: Clean up the temporary database
        print("\nStep 5: Cleaning up the temporary database")
        cleanup_database(db_name)
    
    # Step 6: Clean up the dump file if not keeping it
    if not keep_dump:
        print("\nStep 6: Cleaning up the dump file")
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
