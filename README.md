# dungeonchurch-oracle
This repo creates a D3 network visualization of the relationships in the Dungeon Church lore wiki.

## Setup

### Prerequisites
- Python 3.6+
- PostgreSQL client tools (pg_restore, createdb, dropdb)
- psycopg2 Python package (`pip install psycopg2-binary`)
- requests Python package (`pip install requests`)

### Environment Variables
Set the following environment variables:
```
DUNGEONCHURCH_S3_URL=<pre-authenticated request URL for OCI Object Storage>
DUNGEONCHURCH_S3_NAMESPACE=<OCI namespace>
DUNGEONCHURCH_S3_BUCKET=<OCI bucket name>
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

## Automated Updates

This repository includes a GitHub Actions workflow that:
1. Runs daily at midnight UTC (and can be triggered manually)
2. Downloads the latest database dump
3. Processes the relationship data if download is successful
4. Commits and pushes the updated graph_data.json file
5. Cleans up the dump file to ensure sensitive data isn't stored

The workflow requires the following GitHub secrets:
- `DUNGEONCHURCH_S3_URL`
- `DUNGEONCHURCH_S3_NAMESPACE`
- `DUNGEONCHURCH_S3_BUCKET`

# To Do
Use `OUTLINE_API_TOKEN` and `OUTLINE_URL`
