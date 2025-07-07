# Static Templates for Dungeon Church Oracle

This folder contains the static templates used to generate the Dungeon Church Oracle visualization.

## Structure

- `index.html` - The main HTML template
- `css/styles.css` - The CSS styles for the visualization
- `js/visualization.js` - The JavaScript code for the D3.js visualization

## How to Use

1. **Local Development**:
   - Edit these files to customize the visualization
   - Run `python scripts/create_viz.py` to generate the visualization in the `docs` folder
   - Open `docs/index.html` in your browser to preview the changes

2. **Deployment**:
   - Changes to files in this folder will automatically trigger a rebuild and deployment via GitHub Actions
   - The GitHub Actions workflow will run `create_viz.py` and deploy the generated files to GitHub Pages

## Notes

- The graph data is not stored in this folder. It's generated from `data/graph_data.json` by the `create_viz.py` script.
- The `create_viz.py` script will:
  - Generate a `graph-data.js` file with the graph data
  - Copy these template files to the `docs` folder
  - Deploy the `docs` folder to GitHub Pages

## Adding Custom Features

To add custom features to the visualization:

1. Edit the appropriate files in this folder
2. Test locally by running `python scripts/create_viz.py` and opening `docs/index.html`
3. Commit and push your changes
4. The GitHub Actions workflow will automatically deploy your changes to GitHub Pages

