# Data Pipeline Scripts

This directory contains scripts for the Dungeon Church Oracle data pipeline.

## Scripts Overview

### `run_pipeline.py`

The main script that orchestrates the entire data pipeline. It runs the following steps:
1. Download the latest database dump
2. Process the dump to extract relationship data
3. Process collection colors for visualization
4. Clean up the dump file (optional)

Usage:
```bash
python run_pipeline.py [--output OUTPUT_FILE] [--keep-dump]
```

### `download_latest_dump.py`

Downloads the latest PostgreSQL dump file from the S3 bucket.

### `process_relationships.py`

Processes the PostgreSQL dump file to extract relationship data for the D3 visualization.

### `process_colors.py`

Extracts collection colors from the database and generates CSS and JavaScript files for the visualization.

Usage:
```bash
python process_colors.py DB_NAME [--css-output CSS_FILE] [--js-output JS_FILE]
```

### `create_viz.py`

Creates the D3.js network visualization from the graph data and copies all necessary files to the docs directory.

## Data Pipeline Flow

1. The pipeline starts by downloading the latest database dump from S3.
2. It then restores the dump to a temporary PostgreSQL database.
3. Relationship data is extracted from the database and saved as `data/graph_data.json`.
4. Collection colors are extracted from the database and saved as CSS and JavaScript files.
5. The visualization files are generated in the `docs` directory.
6. The temporary database and dump file are cleaned up.

## Collection Colors

The `process_colors.py` script extracts color information for each collection from the database and generates:

1. A CSS file (`static/css/collection-colors.css`) with CSS variables and classes for each collection.
2. A JavaScript file (`static/js/collection-colors.js`) with a mapping of collection IDs to their hex color codes.

These files are then used by the visualization to color nodes based on their collection.

