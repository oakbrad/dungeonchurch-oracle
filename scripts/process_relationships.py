#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
import tempfile
import shutil
import argparse

def restore_database(dump_file):
    """
    Restore the PostgreSQL dump file to a temporary database.
    
    Args:
        dump_file (str): Path to the PostgreSQL dump file
        
    Returns:
        str: Name of the temporary database, or None if restoration failed
    """
    try:
        # Create a temporary database name
        temp_db_name = f"outline_temp_{os.path.basename(dump_file).split('.')[0]}"
        
        print(f"Creating temporary database: {temp_db_name}")
        
        # Get PostgreSQL connection parameters from environment variables
        pg_host = os.environ.get("POSTGRES_HOST", "localhost")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_user = os.environ.get("POSTGRES_USER", "postgres")
        pg_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        
        # Set PGPASSWORD environment variable for command-line tools
        pg_env = os.environ.copy()
        pg_env["PGPASSWORD"] = pg_password
        
        # Create the database
        subprocess.run([
            "createdb",
            "-h", pg_host,
            "-p", pg_port,
            "-U", pg_user,
            temp_db_name
        ], check=True, env=pg_env)
        
        # Restore the dump file to the temporary database
        print(f"Restoring dump file to database: {temp_db_name}")
        result = subprocess.run([
            "pg_restore",
            "-h", pg_host,
            "-p", pg_port,
            "-U", pg_user,
            "-d", temp_db_name,
            "--no-owner",  # Skip ownership commands
            "--no-privileges",  # Skip privilege commands
            dump_file
        ], capture_output=True, text=True, env=pg_env)
        
        # pg_restore often returns non-zero exit codes even when successful
        # due to warnings, so we check if the database was created
        if result.returncode != 0:
            print("Warning: pg_restore returned non-zero exit code")
            # Only print first few lines of stderr to avoid overwhelming logs
            stderr_lines = result.stderr.split('\n')
            if len(stderr_lines) > 10:
                print("stderr (first 10 lines):")
                for i in range(10):
                    print(stderr_lines[i])
                print(f"... and {len(stderr_lines) - 10} more lines")
            else:
                print(f"stderr: {result.stderr}")
            
        # Create the materialized views
        print("Creating materialized views for graph nodes and edges")
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            dbname=temp_db_name
        )
        cursor = conn.cursor()
        
        # Create graph_nodes view
        cursor.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS graph_nodes AS
        SELECT id, title, "urlId", "collectionId"
        FROM   documents
        WHERE  "deletedAt" IS NULL;
        """)
        
        # Create graph_edges view
        cursor.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS graph_edges AS
        SELECT "reverseDocumentId" AS source,
               "documentId"        AS target
        FROM   relationships
        WHERE  type = 'backlink';
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return temp_db_name
        
    except subprocess.CalledProcessError as e:
        print(f"Error restoring database: {e}")
        print(f"stderr: {e.stderr if hasattr(e, 'stderr') else 'None'}")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def extract_relationship_data(db_name):
    """
    Extract relationship data from the database and create a D3-compatible JSON file.
    
    Args:
        db_name (str): Name of the database to extract data from
        
    Returns:
        dict: D3-compatible graph data, or None if extraction failed
    """
    try:
        # Get PostgreSQL connection parameters from environment variables
        pg_host = os.environ.get("POSTGRES_HOST", "localhost")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_user = os.environ.get("POSTGRES_USER", "postgres")
        pg_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        
        print(f"Connecting to database: {db_name}")
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            dbname=db_name
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Extract nodes
        print("Extracting nodes data")
        cursor.execute("SELECT * FROM graph_nodes")
        all_nodes = cursor.fetchall()
        
        # Extract edges
        print("Extracting edges data")
        cursor.execute("SELECT * FROM graph_edges")
        all_links = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Filter out nodes from the private collection
        private_collection_id = "9870bc72-55da-4158-892c-3c54ec9e5828"
        print(f"Filtering out nodes from private collection: {private_collection_id}")
        nodes = [node for node in all_nodes if node['collectionId'] != private_collection_id]
        
        # Check if we should exclude the 5E collection based on the EXCLUDE_5E environment variable
        exclude_5e = os.environ.get("EXCLUDE_5E", "").lower() == "true"
        if exclude_5e:
            five_e_collection_id = "7275a3d8-27da-4f63-ac39-a9bc9a1ec6d7"
            print(f"EXCLUDE_5E is set to true. Filtering out nodes from 5E collection: {five_e_collection_id}")
            nodes = [node for node in nodes if node['collectionId'] != five_e_collection_id]
        
        # Get the IDs of nodes to include
        node_ids = {node['id'] for node in nodes}
        
        # Filter out links that connect to excluded nodes
        print("Filtering out links connected to excluded collection nodes")
        links = [link for link in all_links 
                if link['source'] in node_ids and link['target'] in node_ids]
        
        # Convert to D3-compatible format
        graph_data = {
            "nodes": [dict(node) for node in nodes],
            "links": [dict(link) for link in links]
        }
        
        print(f"Filtered out {len(all_nodes) - len(nodes)} nodes from excluded collections")
        print(f"Filtered out {len(all_links) - len(links)} links connected to excluded collection nodes")
        
        return graph_data
        
    except Exception as e:
        print(f"Error extracting relationship data: {str(e)}")
        return None

def cleanup_database(db_name):
    """
    Drop the temporary database.
    
    Args:
        db_name (str): Name of the database to drop
    """
    try:
        # Get PostgreSQL connection parameters from environment variables
        pg_host = os.environ.get("POSTGRES_HOST", "localhost")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_user = os.environ.get("POSTGRES_USER", "postgres")
        pg_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        
        # Set PGPASSWORD environment variable for command-line tools
        pg_env = os.environ.copy()
        pg_env["PGPASSWORD"] = pg_password
        
        print(f"Dropping temporary database: {db_name}")
        subprocess.run([
            "dropdb",
            "-h", pg_host,
            "-p", pg_port,
            "-U", pg_user,
            db_name
        ], check=True, env=pg_env)
        print("Database dropped successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error dropping database: {e}")
        print(f"stderr: {e.stderr if hasattr(e, 'stderr') else 'None'}")
    except Exception as e:
        print(f"Error: {str(e)}")

def process_relationships(dump_file, output_file=None):
    """
    Process the PostgreSQL dump file and extract relationship data into a D3-compatible JSON file.
    
    Args:
        dump_file (str): Path to the PostgreSQL dump file
        output_file (str, optional): Path to the output JSON file. If None, a default path will be used.
        
    Returns:
        str: Path to the output JSON file, or None if processing failed
    """
    if not os.path.exists(dump_file):
        print(f"Error: Dump file not found: {dump_file}")
        return None
    
    # Set default output file if not provided
    if output_file is None:
        # Create a data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        output_file = os.path.join(data_dir, "graph_data.json")
    
    # Restore the database
    db_name = restore_database(dump_file)
    if not db_name:
        print("Failed to restore database")
        return None
    
    try:
        # Extract relationship data
        graph_data = extract_relationship_data(db_name)
        if not graph_data:
            print("Failed to extract relationship data")
            return None
        
        # Save the data to a JSON file
        print(f"Saving graph data to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"Graph data saved successfully")
        print(f"Nodes: {len(graph_data['nodes'])}")
        print(f"Links: {len(graph_data['links'])}")
        
        return output_file
        
    finally:
        # Clean up the temporary database
        cleanup_database(db_name)

def main():
    parser = argparse.ArgumentParser(description='Process PostgreSQL dump file and extract relationship data for D3 visualization')
    parser.add_argument('dump_file', help='Path to the PostgreSQL dump file')
    parser.add_argument('--output', '-o', help='Path to the output JSON file')
    
    args = parser.parse_args()
    
    output_file = process_relationships(args.dump_file, args.output)
    if output_file:
        print(f"Successfully processed dump file and saved graph data to: {output_file}")
    else:
        print("Failed to process dump file")
        sys.exit(1)

if __name__ == "__main__":
    main()
