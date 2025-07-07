#!/usr/bin/env python3
"""
Script to create a D3.js network visualization from graph data.
This script reads the relationship data from data/graph_data.json
and generates an HTML file with a D3.js visualization.
"""

import json
import os
import shutil
from pathlib import Path

def create_visualization():
    """
    Create a D3.js network visualization from the graph data.
    """
    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Read the graph data
    with open("data/graph_data.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    
    # Create the HTML file with D3.js visualization
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dungeon Church Oracle - Network Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1a1a1a;
            color: #f0f0f0;
        }}
        #visualization {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        .node {{
            cursor: pointer;
        }}
        .node circle {{
            fill: #69b3a2;
            stroke: #fff;
            stroke-width: 1.5px;
        }}
        .node text {{
            font-size: 10px;
            fill: #fff;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        .tooltip {{
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            font-size: 14px;
            max-width: 300px;
        }}
        #search-container {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
        }}
        #search-input {{
            padding: 8px;
            width: 250px;
            border-radius: 4px;
            border: 1px solid #555;
            background-color: #333;
            color: #fff;
        }}
        #search-results {{
            background-color: #333;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
            width: 250px;
            display: none;
        }}
        .search-result {{
            padding: 8px;
            cursor: pointer;
            border-bottom: 1px solid #555;
            color: #fff;
        }}
        .search-result:hover {{
            background-color: #444;
        }}
    </style>
</head>
<body>
    <div id="search-container">
        <input type="text" id="search-input" placeholder="Search nodes...">
        <div id="search-results"></div>
    </div>
    <div id="visualization"></div>
    
    <script>
    // Graph data from JSON
    const graphData = {graph_data};
    
    // Create a map for quick node lookup
    const nodeMap = new Map();
    graphData.nodes.forEach(node => {{
        nodeMap.set(node.id, node);
    }});
    
    // Setup the visualization
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Create tooltip
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);
    
    // Create SVG
    const svg = d3.select("#visualization")
        .append("svg")
        .attr("width", width)
        .attr("height", height);
    
    // Create a group for zoom/pan
    const g = svg.append("g");
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on("zoom", (event) => {{
            g.attr("transform", event.transform);
        }});
    
    svg.call(zoom);
    
    // Center the view initially
    svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5));
    
    // Create the force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.links)
            .id(d => d.id)
            .distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(0, 0))
        .force("collide", d3.forceCollide(30));
    
    // Create links
    const link = g.append("g")
        .selectAll("line")
        .data(graphData.links)
        .enter().append("line")
        .attr("class", "link")
        .attr("stroke-width", d => Math.sqrt(d.value || 1));
    
    // Create nodes
    const node = g.append("g")
        .selectAll(".node")
        .data(graphData.nodes)
        .enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
    
    // Add circles to nodes
    node.append("circle")
        .attr("r", d => 5 + (d.connections ? Math.sqrt(d.connections) * 2 : 5))
        .attr("fill", d => getNodeColor(d))
        .on("mouseover", function(event, d) {{
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            
            // Get connected nodes
            const connectedLinks = graphData.links.filter(link => 
                link.source.id === d.id || link.target.id === d.id
            );
            
            const connectedNodes = connectedLinks.map(link => {{
                const connectedId = link.source.id === d.id ? link.target.id : link.source.id;
                const connectedNode = nodeMap.get(connectedId);
                return {{
                    title: connectedNode.title,
                    relationship: link.relationship || "connected to"
                }};
            }});
            
            // Build tooltip content
            let tooltipContent = `<strong>${d.title}</strong><br>`;
            if (connectedNodes.length > 0) {{
                tooltipContent += "<br><strong>Connections:</strong><br>";
                connectedNodes.slice(0, 10).forEach(conn => {{
                    tooltipContent += `• ${conn.relationship} <em>${conn.title}</em><br>`;
                }});
                
                if (connectedNodes.length > 10) {{
                    tooltipContent += `<em>...and ${connectedNodes.length - 10} more</em>`;
                }}
            }}
            
            tooltip.html(tooltipContent)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function() {{
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        }});
    
    // Add labels to nodes
    node.append("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(d => truncateText(d.title, 20))
        .style("opacity", 0.7);
    
    // Update positions on each tick
    simulation.on("tick", () => {{
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    }});
    
    // Helper functions
    function dragstarted(event, d) {{
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }}
    
    function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
    }}
    
    function dragended(event, d) {{
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }}
    
    function getNodeColor(node) {{
        // Color nodes based on collection
        const collections = {{
            "13b87098-500c-490d-ae46-01356387fe88": "#ff7f0e", // Adventures
            "7275a3d8-27da-4f63-ac39-a9bc9a1ec6d7": "#1f77b4", // Spells
            // Add more collections as needed
        }};
        
        return collections[node.collectionId] || "#69b3a2";
    }}
    
    function truncateText(text, maxLength) {{
        return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
    }}
    
    // Search functionality
    const searchInput = document.getElementById("search-input");
    const searchResults = document.getElementById("search-results");
    
    searchInput.addEventListener("input", function() {{
        const query = this.value.toLowerCase();
        
        if (query.length < 2) {{
            searchResults.style.display = "none";
            return;
        }}
        
        // Filter nodes based on search query
        const matchingNodes = graphData.nodes.filter(node => 
            node.title.toLowerCase().includes(query)
        ).slice(0, 10); // Limit to 10 results
        
        // Display results
        if (matchingNodes.length > 0) {{
            searchResults.innerHTML = "";
            matchingNodes.forEach(node => {{
                const resultItem = document.createElement("div");
                resultItem.className = "search-result";
                resultItem.textContent = node.title;
                resultItem.addEventListener("click", function() {{
                    // Find the node in the visualization
                    const selectedNode = node;
                    
                    // Center view on the selected node
                    svg.transition().duration(750).call(
                        zoom.transform,
                        d3.zoomIdentity
                            .translate(width / 2, height / 2)
                            .scale(1)
                            .translate(-selectedNode.x, -selectedNode.y)
                    );
                    
                    // Clear search
                    searchInput.value = "";
                    searchResults.style.display = "none";
                }});
                searchResults.appendChild(resultItem);
            }});
            searchResults.style.display = "block";
        }} else {{
            searchResults.innerHTML = "<div class='search-result'>No results found</div>";
            searchResults.style.display = "block";
        }}
    }});
    
    // Close search results when clicking outside
    document.addEventListener("click", function(event) {{
        if (event.target !== searchInput && !searchResults.contains(event.target)) {{
            searchResults.style.display = "none";
        }}
    }});
    </script>
</body>
</html>
"""
    
    # Write the HTML file
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
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

