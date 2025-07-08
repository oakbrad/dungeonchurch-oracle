# Dungeon Church Oracle - Static Template

This directory contains the static template files for the Dungeon Church Oracle visualization.

## Overview

The Dungeon Church Oracle is an interactive network visualization of wiki content. It displays relationships between different pages in the wiki as a force-directed graph.

## Features

- Interactive network graph with zoom and pan functionality
- Search for specific nodes
- Hover for detailed information
- Color-coded nodes by collection
- Responsive design for embedding in other websites

## Files

- `index.html` - The main HTML template
- `css/styles.css` - Main CSS styles
- `css/collection-colors.css` - CSS for collection-specific colors
- `js/visualization.js` - D3.js visualization code
- `js/collection-colors.js` - JavaScript for collection colors
- `embed-example.html` - Example showing how to embed the visualization

## Embedding

The visualization is designed to be embedded in other websites as an interactive element. It will automatically adapt to fill its container without scrollbars.

### Basic Embedding

To embed the visualization in your website, use an iframe:

```html
<div style="width: 100%; height: 500px; overflow: hidden;">
  <iframe src="https://oakbrad.github.io/dungeonchurch-oracle/" width="100%" height="100%" frameborder="0"></iframe>
</div>
```

You can adjust the width and height of the container to fit your layout.

### Advanced: Container Resizing

If your container size changes dynamically (e.g., in responsive layouts or when toggling UI elements), you can notify the visualization using the postMessage API:

```javascript
// Get a reference to the iframe
const iframe = document.querySelector('iframe');

// Send a resize message to the visualization
iframe.contentWindow.postMessage({ type: 'resize' }, '*');
```

This ensures the visualization properly updates its dimensions when its container changes size.

### Example

See `embed-example.html` for a complete example of embedding the visualization in different container sizes.

## Development

The visualization is generated using data from `data/graph_data.json`. The Python script `scripts/create_viz.py` processes this data and creates the visualization files in the `docs` directory.

To modify the visualization:

1. Edit the files in the `static` directory
2. Run `scripts/create_viz.py` to generate the updated visualization
3. The updated visualization will be available in the `docs` directory

