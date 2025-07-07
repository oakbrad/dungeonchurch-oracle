#!/usr/bin/env python3
"""
Script to extract collection colors from the database and create a CSS file.
This script queries the database for collections and their associated color hex codes,
then generates a CSS file that can be used by the visualization.
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
from pathlib import Path

def extract_collection_colors(db_name):
    """
    Extract collection colors from the database.
    
    Args:
        db_name (str): Name of the database to extract data from
        
    Returns:
        dict: Dictionary mapping collection IDs to their hex color codes
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
        
        # Extract collections with their colors
        print("Extracting collection colors")
        
        # Query to get collections and their colors
        # Note: The actual column name for color might be different
        # Adjust the query based on the actual schema
        cursor.execute("""
        SELECT id, name, color
        FROM collections
        WHERE "deletedAt" IS NULL;
        """)
        
        collections = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create a dictionary mapping collection IDs to colors
        collection_colors = {}
        for collection in collections:
            # If color is not set, use a default color
            color = collection.get('color', '#69b3a2')
            
            # Ensure color is a valid hex code
            if color and not color.startswith('#'):
                color = f"#{color}"
                
            collection_colors[collection['id']] = {
                'name': collection['name'],
                'color': color
            }
        
        print(f"Extracted colors for {len(collection_colors)} collections")
        return collection_colors
        
    except Exception as e:
        print(f"Error extracting collection colors: {str(e)}")
        return None

def generate_css(collection_colors, output_file):
    """
    Generate a CSS file with collection colors.
    
    Args:
        collection_colors (dict): Dictionary mapping collection IDs to their hex color codes
        output_file (str): Path to the output CSS file
        
    Returns:
        bool: True if the CSS file was generated successfully, False otherwise
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Generate CSS content
        css_content = "/* Auto-generated collection colors */\n\n"
        
        # Add CSS variables for each collection
        css_content += ":root {\n"
        for collection_id, data in collection_colors.items():
            css_content += f"    --collection-{collection_id}: {data['color']};\n"
        css_content += "}\n\n"
        
        # Add classes for each collection
        for collection_id, data in collection_colors.items():
            css_content += f"/* {data['name']} */\n"
            css_content += f".collection-{collection_id} {{\n"
            css_content += f"    fill: {data['color']};\n"
            css_content += f"    color: {data['color']};\n"
            css_content += "}\n\n"
        
        # Write the CSS file
        with open(output_file, 'w') as f:
            f.write(css_content)
        
        print(f"CSS file generated successfully: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error generating CSS file: {str(e)}")
        return False

def generate_js_colors(collection_colors, output_file):
    """
    Generate a JavaScript file with collection colors.
    
    Args:
        collection_colors (dict): Dictionary mapping collection IDs to their hex color codes
        output_file (str): Path to the output JavaScript file
        
    Returns:
        bool: True if the JavaScript file was generated successfully, False otherwise
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Create a simplified dictionary with just the colors
        colors_dict = {collection_id: data['color'] for collection_id, data in collection_colors.items()}
        
        # Generate JavaScript content
        js_content = "// Auto-generated collection colors\n\n"
        js_content += "const collectionColors = " + json.dumps(colors_dict, indent=2) + ";\n\n"
        js_content += "// Function to get color for a collection\n"
        js_content += "function getCollectionColor(collectionId) {\n"
        js_content += "    return collectionColors[collectionId] || '#69b3a2';\n"
        js_content += "}\n"
        
        # Write the JavaScript file
        with open(output_file, 'w') as f:
            f.write(js_content)
        
        print(f"JavaScript colors file generated successfully: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error generating JavaScript colors file: {str(e)}")
        return False

def process_colors(db_name, css_output=None, js_output=None):
    """
    Process collection colors from the database and generate CSS and JS files.
    
    Args:
        db_name (str): Name of the database to extract data from
        css_output (str, optional): Path to the output CSS file. If None, a default path will be used.
        js_output (str, optional): Path to the output JavaScript file. If None, a default path will be used.
        
    Returns:
        tuple: (css_file, js_file) paths to the generated files, or (None, None) if processing failed
    """
    # Set default output files if not provided
    if css_output is None:
        # Create a static/css directory if it doesn't exist
        css_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "css")
        os.makedirs(css_dir, exist_ok=True)
        css_output = os.path.join(css_dir, "collection-colors.css")
    
    if js_output is None:
        # Create a static/js directory if it doesn't exist
        js_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "js")
        os.makedirs(js_dir, exist_ok=True)
        js_output = os.path.join(js_dir, "collection-colors.js")
    
    # Extract collection colors from the database
    collection_colors = extract_collection_colors(db_name)
    if not collection_colors:
        print("Failed to extract collection colors")
        return None, None
    
    # Generate CSS file
    css_success = generate_css(collection_colors, css_output)
    if not css_success:
        print("Failed to generate CSS file")
        css_output = None
    
    # Generate JavaScript file
    js_success = generate_js_colors(collection_colors, js_output)
    if not js_success:
        print("Failed to generate JavaScript file")
        js_output = None
    
    return css_output, js_output

def main():
    parser = argparse.ArgumentParser(description='Process collection colors from the database and generate CSS and JS files')
    parser.add_argument('db_name', help='Name of the database to extract data from')
    parser.add_argument('--css-output', '-c', help='Path to the output CSS file')
    parser.add_argument('--js-output', '-j', help='Path to the output JavaScript file')
    
    args = parser.parse_args()
    
    css_file, js_file = process_colors(args.db_name, args.css_output, args.js_output)
    if css_file and js_file:
        print(f"Successfully processed collection colors and saved to:")
        print(f"CSS: {css_file}")
        print(f"JS: {js_file}")
    else:
        print("Failed to process collection colors")
        sys.exit(1)

if __name__ == "__main__":
    main()

