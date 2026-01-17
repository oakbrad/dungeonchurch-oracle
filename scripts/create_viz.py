#!/usr/bin/env python3
"""
Script to create a D3.js network visualization from graph data.
This script reads the relationship data from data/graph_data.json
and generates visualization files in the docs directory using templates
from the static directory.
"""

import json
import os
import shutil
from pathlib import Path

def create_visualization():
    """
    Create a D3.js network visualization from the graph data.
    Uses templates from the static directory and outputs to the docs directory.
    """
    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Read the graph data
    with open("data/graph_data.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    
    # Create the graph data JavaScript file
    graph_data_js = f"// Graph data from JSON\nconst graphData = {json.dumps(graph_data, indent=2)};"
    
    # Create the docs/js directory if it doesn't exist
    docs_js_dir = docs_dir / "js"
    docs_js_dir.mkdir(exist_ok=True)
    
    # Write the graph data JavaScript file
    with open(docs_js_dir / "graph-data.js", "w", encoding="utf-8") as f:
        f.write(graph_data_js)
    
    # Create the docs/css directory if it doesn't exist
    docs_css_dir = docs_dir / "css"
    docs_css_dir.mkdir(exist_ok=True)
    
    # Copy static files to docs directory
    # Copy CSS
    shutil.copy("static/css/styles.css", docs_css_dir / "styles.css")
    
    # Copy collection colors CSS if it exists
    collection_colors_css = Path("static/css/collection-colors.css")
    if collection_colors_css.exists():
        shutil.copy(collection_colors_css, docs_css_dir / "collection-colors.css")
        print("Collection colors CSS copied to docs/css/collection-colors.css")

    # Copy alignment mode CSS if it exists
    alignment_mode_css = Path("static/css/alignment-mode.css")
    if alignment_mode_css.exists():
        shutil.copy(alignment_mode_css, docs_css_dir / "alignment-mode.css")
        print("Alignment mode CSS copied to docs/css/alignment-mode.css")
    
    # Copy visualization.js
    shutil.copy("static/js/visualization.js", docs_js_dir / "visualization.js")
    
    # Copy collection colors JS if it exists
    collection_colors_js = Path("static/js/collection-colors.js")
    if collection_colors_js.exists():
        shutil.copy(collection_colors_js, docs_js_dir / "collection-colors.js")
        print("Collection colors JS copied to docs/js/collection-colors.js")
    
    # Copy index.html
    shutil.copy("static/index.html", docs_dir / "index.html")
    
    # Create a simple README for the GitHub Pages site
    readme_content = """# Dungeon Church Oracle

This is an interactive network visualization of the Dungeon Church wiki content.

The visualization shows the relationships between different pages in the wiki.

## Features

- Interactive network graph
- Zoom and pan functionality
- Search for specific nodes
- Hover for detailed information
- Color-coded by collection

This visualization is automatically updated daily with the latest data from the wiki.
"""
    
    with open("docs/README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("Visualization created successfully in docs/index.html")
    return True

if __name__ == "__main__":
    create_visualization()
