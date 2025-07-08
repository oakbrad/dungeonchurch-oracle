#!/usr/bin/env python3
import os
import json
import argparse
import sys

def test_relationship_metadata(graph_data_file):
    """
    Test that the graph_data.json file contains the expected relationship metadata.
    
    Args:
        graph_data_file (str): Path to the graph_data.json file
        
    Returns:
        bool: True if the test passes, False otherwise
    """
    if not os.path.exists(graph_data_file):
        print(f"Error: Graph data file not found: {graph_data_file}")
        return False
    
    try:
        # Load the graph data
        with open(graph_data_file, 'r') as f:
            graph_data = json.load(f)
        
        # Check that the graph data has the expected structure
        if 'nodes' not in graph_data:
            print("Error: Graph data does not contain 'nodes' key")
            return False
        
        if 'links' not in graph_data:
            print("Error: Graph data does not contain 'links' key")
            return False
        
        # Check that there are links
        if not graph_data['links']:
            print("Warning: Graph data contains no links")
            return False
        
        # Check that the links have the expected metadata
        metadata_fields = ['creation_time', 'direction']
        missing_fields = []
        
        # Check the first link
        first_link = graph_data['links'][0]
        for field in metadata_fields:
            if field not in first_link:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Error: Links are missing the following metadata fields: {', '.join(missing_fields)}")
            print(f"First link: {first_link}")
            return False
        
        # Print some statistics
        print(f"Graph data loaded successfully from: {graph_data_file}")
        print(f"Nodes: {len(graph_data['nodes'])}")
        print(f"Links: {len(graph_data['links'])}")
        
        # Print metadata for the first few links
        print("\nSample link metadata:")
        for i, link in enumerate(graph_data['links'][:5]):
            print(f"Link {i+1}:")
            print(f"  Source: {link['source']}")
            print(f"  Target: {link['target']}")
            print(f"  Creation Time: {link.get('creation_time', 'N/A')}")
            print(f"  Direction: {link.get('direction', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error testing relationship metadata: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test that the graph_data.json file contains the expected relationship metadata')
    parser.add_argument('--graph-data', '-g', default='data/graph_data.json', help='Path to the graph_data.json file')
    
    args = parser.parse_args()
    
    success = test_relationship_metadata(args.graph_data)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()

