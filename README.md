<p align="center">
    <img width="650" src="https://raw.githubusercontent.com/oakbrad/dungeonchurch/refs/heads/main/logo-chrome.png"><br>
    <a href=https://github.com/oakbrad/dungeonchurch>
        <img src=https://img.shields.io/github/last-commit/oakbrad/dungeonchurch?label=dungeonchurch&color=gray&labelColor=ff2600&logoColor=ffffff&logo=docker></a>
    <a href=https://github.com/oakbrad/dungeonchurch-pyora>
        <img src=https://img.shields.io/github/last-commit/oakbrad/dungeonchurch-pyora?label=dungeonchurch-pyora&color=gray&labelColor=ff2600&logo=dungeonsanddragons></a>
    <a href=https://github.com/oakbrad/dungeonchurch-basilica>
        <img src=https://img.shields.io/github/last-commit/oakbrad/dungeonchurch-basilica?label=dungeonchurch-basilica&color=gray&labelColor=ff2600&logo=ghost></a>
    <a href=https://github.com/oakbrad/dungeonchurch-cogs>
        <img src=https://img.shields.io/github/last-commit/oakbrad/dungeonchurch-cogs?label=dungeonchurch-cogs&color=gray&labelColor=ff2600&logoColor=ffffff&logo=discord></a>
</p>

# Oracle
This repo automates the creation of [D3js](https://d3js.org/) visualizations based on Dungeon Church [lore wiki](https://lore.dungeon.church) data.

[The result](https://oakbrad.github.io/dungeonchurch-oracle/) is deployed on GH pages.

## Repository Structure

- `data/` - Contains the graph data JSON file
- `scripts/` - Python scripts for data processing and visualization generation
- `static/` - Static templates for the visualization (HTML, CSS, JS)
- `docs/` - Generated files for GitHub Pages deployment (created by scripts, not stored in the repository)

## Setup
[Outline](https://github.com/outline/outline) database [nightly backups](https://github.com/oakbrad/dungeonchurch/blob/81f2a3a4e5cf00af524ad6a5d0c33f967a0edd74/docker-compose.yaml#L174) are stored in a private S3 bucket:
```
DUNGEONCHURCH_S3_URL=<pre-authenticated request URL for OCI Object Storage>
DUNGEONCHURCH_S3_NAMESPACE=<OCI namespace>
DUNGEONCHURCH_S3_BUCKET=<OCI bucket name>
```
The 5E rules collection in the wiki can be included or excluded in the visualization with:
```
EXCLUDE_5E=true
```
For future Outline integration:
```
OUTLINE_API_TOKEN=xxx
OUTLINE_URL=https://lore.dungeon.church/api
```
## Process
### Download the Latest Database Dump
```bash
python scripts/download_latest_dump.py
```
This will download the latest PostgreSQL dump file from OCI S3 compatible storage and save it to the `data` directory.

### Process Relationship Data
```bash
python scripts/process_relationships.py <path_to_dump_file>
```
1. Restore the PostgreSQL dump file to a temporary database
2. Extract document relationship data
3. Save the data as a JSON file in the `data` directory
4. Drop the temporary database

### Create Visualization
```bash
python scripts/create_viz.py
```
1. Generate the visualization files in the `docs` folder using templates from the `static` folder
2. The `docs` folder is not stored in the repository but is generated on-demand

### Run the Complete Pipeline
```bash
python scripts/run_pipeline.py
```
1. Download the latest database dump
2. Process the dump to extract relationship data
3. Clean up the dump file (unless `--keep-dump` is specified)

Options:
- `--output` or `-o`: Specify the output JSON file path
- `--keep-dump` or `-k`: Keep the dump file after processing

## Customizing the Visualization

The visualization can be customized by editing the files in the `static` folder:

- `static/index.html` - The main HTML template
- `static/css/styles.css` - The CSS styles for the visualization
- `static/js/visualization.js` - The JavaScript code for the D3.js visualization

After making changes to these files, you can:

1. Run `python scripts/create_viz.py` to generate the updated visualization in the `docs` folder
2. Open `docs/index.html` in your browser to preview the changes
3. Commit and push your changes to deploy them via GitHub Actions

## Automated Updates
This repository includes GitHub Actions workflows that:

1. Run the data pipeline daily at midnight UTC (and can be triggered manually)
2. Rebuild and deploy the visualization when changes are made to:
   - The graph data (`data/graph_data.json`)
   - The static templates (`static/*`)
   - The visualization script (`scripts/create_viz.py`)

