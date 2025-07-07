# Dungeon Church Oracle

This repository creates a D3 network visualization of the relationships in the Dungeon Church lore wiki.

## Live Visualization

The network visualization is automatically published to GitHub Pages and can be viewed at:
[https://oakbrad.github.io/dungeonchurch-oracle/](https://oakbrad.github.io/dungeonchurch-oracle/)

## Overview

The Oracle system performs the following tasks:
1. Downloads a PostgreSQL database dump from Oracle Cloud Infrastructure (OCI) Object Storage
2. Processes the dump to extract relationship data between wiki pages
3. Creates an interactive D3.js network visualization
4. Publishes the visualization to GitHub Pages

## Setup

### Prerequisites
- Python 3.6+
- PostgreSQL client tools (pg_restore, createdb, dropdb)
- psycopg2 Python package (`pip install psycopg2-binary`)
- requests Python package (`pip install requests`)

### Environment Variables
Set the following environment variables for OCI S3 compatible storage access:
```
DUNGEONCHURCH_S3_URL=<pre-authenticated request URL for OCI Object Storage>
DUNGEONCHURCH_S3_NAMESPACE=<OCI namespace>
DUNGEONCHURCH_S3_BUCKET=<OCI bucket name>
```

For PostgreSQL configuration (optional, defaults shown):
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

For data filtering (optional):
```
EXCLUDE_5E=true  # Set to "true" to exclude 5E-related content
```

For GitHub Actions, add these as repository secrets.

## Usage

### Download the Latest Database Dump
```bash
python scripts/download_latest_dump.py
```
This will download the latest PostgreSQL dump file from OCI S3 compatible storage and save it to the `data` directory.

### Process Relationship Data
```bash
python scripts/process_relationships.py <path_to_dump_file>
```
This will:
1. Restore the PostgreSQL dump file to a temporary database
2. Extract document relationship data
3. Save the data as a JSON file in the `data` directory
4. Drop the temporary database

### Create Visualization
```bash
python scripts/create_viz.py
```
This will:
1. Read the processed relationship data from `data/graph_data.json`
2. Generate an interactive D3.js visualization
3. Save the visualization as HTML in the `docs` directory

### Run the Complete Pipeline
```bash
python scripts/run_pipeline.py
```
This will:
1. Download the latest database dump
2. Process the dump to extract relationship data
3. Clean up the dump file (unless `--keep-dump` is specified)

Options:
- `--output` or `-o`: Specify the output JSON file path
- `--keep-dump` or `-k`: Keep the dump file after processing

## Automated Workflows

This repository includes several GitHub Actions workflows:

### Data Pipeline (data-pipeline.yml)
- Runs daily at midnight UTC (and can be triggered manually)
- Downloads the latest database dump
- Processes the relationship data if download is successful
- Commits and pushes the updated graph_data.json file
- Cleans up the dump file to ensure sensitive data isn't stored

### Visualization Creation (create-visualization.yml)
- Triggered when graph_data.json is updated (or manually)
- Creates the D3.js visualization
- Deploys the visualization to GitHub Pages

### GitHub Pages Setup (pages.yml)
- Ensures GitHub Pages is enabled for the repository
- Creates a placeholder page if no visualization exists yet

The workflows are designed with security in mind:
- All processing happens within a single job to avoid storing sensitive data as artifacts
- The database dump remains only in the runner's temporary file system
- The dump file is deleted after processing, even if the workflow fails
- Only the processed JSON data (which doesn't contain sensitive information) is committed to the repository

## Future Development

### Outline API Integration
Future plans include direct integration with the Outline API using:
- `OUTLINE_API_TOKEN`: Authentication token for the Outline API
- `OUTLINE_URL`: Base URL for the Outline API

This will allow:
1. Direct download of wiki data via the Outline API
2. Real-time updates without requiring database dumps
3. More efficient data processing

## Visualization Features

The generated network visualization includes:
- Interactive network graph with force-directed layout
- Zoom and pan functionality
- Search for specific nodes
- Hover for detailed information
- Color-coding by collection
- Link highlighting on node selection

## Security Considerations

This project handles potentially sensitive wiki data. Security measures include:
- Database dumps are never committed to the repository
- Dumps are deleted after processing
- Only processed relationship data (non-sensitive) is stored in the repository
- Environment variables and secrets are used for all sensitive configuration

