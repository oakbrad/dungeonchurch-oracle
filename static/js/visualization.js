// This file will be populated with graph data by create_viz.py
// The graphData variable will be defined at the top of this file

// Create a map for quick node lookup
const nodeMap = new Map();
graphData.nodes.forEach(node => {
    nodeMap.set(node.id, node);
});

// Setup the visualization
let width = 0;
let height = 0;

// Function to get container dimensions
function getContainerDimensions() {
    const container = document.getElementById('visualization');
    const rect = container.getBoundingClientRect();
    return {
        width: rect.width,
        height: rect.height
    };
}

// Initialize dimensions
const dimensions = getContainerDimensions();
width = dimensions.width;
height = dimensions.height;

// Create tooltip for truncated nodes
const tooltipTruncated = d3.select("body").append("div")
    .attr("class", "tooltip-truncated")
    .style("opacity", 0);

// Create SVG
const svg = d3.select("#visualization")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// Add click handler to SVG to clear highlight state when clicking on the canvas
svg.on("click", function(event) {
    // Only handle clicks directly on the SVG, not on nodes or other elements
    if (event.target === this) {
        // Hide any existing tooltips immediately without transition
        hideTooltipImmediately();
        clearHighlightAndResetZoom();
    }
});

// Create a group for zoom/pan
const g = svg.append("g");

// Add zoom behavior
const zoom = d3.zoom()
    .scaleExtent([0.1, 8])
    .on("zoom", (event) => {
        g.attr("transform", event.transform);
        
        // Update tooltip position if it's visible and we have a highlighted node
        if (parseFloat(tooltipTruncated.style("opacity")) > 0 && highlightedNode) {
            updateTooltipPosition(highlightedNode, event.transform);
        }
    });

svg.call(zoom);

// Center the view initially
svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5));

// Track the currently highlighted node
let highlightedNode = null;

// Function to update tooltip position
function updateTooltipPosition(d, transform) {
    if (!d || !d.isTruncated) return;
    
    const nodeX = d.x;
    const nodeY = d.y;
    const radius = d.radius || 10;
    
    // If no transform is provided, get the current one
    if (!transform) {
        transform = d3.zoomTransform(svg.node());
    }
    
    // Convert node coordinates to screen coordinates
    const screenX = transform.applyX(nodeX);
    const screenY = transform.applyY(nodeY);
    
    // Calculate vertical offset based on node radius and zoom level
    // This ensures the tooltip is always positioned right under the node
    const zoomScale = transform.k;
    const verticalOffset = radius * zoomScale + 5; // 5px additional padding
    
    // Position tooltip centered below the node
    tooltipTruncated
        .style("left", screenX + "px")
        .style("top", (screenY + verticalOffset) + "px");
}

// Function to show tooltip
function showTooltip(d, transform) {
    if (!d || !d.isTruncated) return;
    
    // Update tooltip content
    tooltipTruncated.html("<strong>" + d.title + "</strong>");
    
    // Show the tooltip with transition
    tooltipTruncated.transition()
        .duration(200)
        .style("opacity", 0.9);
    
    // Position the tooltip
    updateTooltipPosition(d, transform);
}

// Function to hide tooltip
function hideTooltip() {
    tooltipTruncated.transition()
        .duration(200)
        .style("opacity", 0);
}

// Function to hide tooltip immediately without transition
function hideTooltipImmediately() {
    tooltipTruncated.style("opacity", 0);
}

// Function to clear highlight state and reset zoom
function clearHighlightAndResetZoom() {

// Function to reorder elements to bring highlighted network to front
function reorderHighlightedElements(currentNode) {
    // First, lower all elements to the back
    node.lower();
    link.lower();
    
    // Then raise elements in order of importance
    // 1. Raise second-order connections
    link.filter(".link-highlight-second").raise();
    node.filter(".node-highlight-second").raise();
    
    // 2. Raise first-order connections
    link.filter(".link-highlight-first").raise();
    node.filter(".node-highlight-first").raise();
    
    // 3. Raise the highlighted node to the top
    currentNode.raise();
}
    if (highlightedNode) {
        // Remove all highlight and dimmed classes
        node.classed("node-highlight", false)
            .classed("node-highlight-first", false)
            .classed("node-highlight-second", false)
            .classed("node-dimmed", false);
        
        link.classed("link-highlight-first", false)
            .classed("link-highlight-second", false)
            .classed("link-dimmed", false);
            
        // Hide tooltip immediately without transition
        hideTooltipImmediately();
            
        // Reset the highlighted node tracker
        highlightedNode = null;
        
        // Reset zoom to default center view
        svg.transition().duration(750).call(
            zoom.transform,
            d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5)
        );
        
        // Reset the rendering order by reappending all nodes and links
        // This effectively resets them to their original order in the DOM
        node.order();
        link.order();
    }
}

// Function to highlight and zoom to a node
function highlightAndZoomToNode(d) {
    // Hide any existing tooltips immediately without transition
    hideTooltipImmediately();
    
    // Set this node as the highlighted node
    highlightedNode = d;
    
    // Get first-order connections
    const firstOrderLinks = graphData.links.filter(link => 
        link.source.id === d.id || link.target.id === d.id
    );
    
    const firstOrderNodeIds = new Set();
    firstOrderLinks.forEach(link => {
        const connectedId = link.source.id === d.id ? link.target.id : link.source.id;
        firstOrderNodeIds.add(connectedId);
    });
    
    // Get all nodes that need to be included in the view
    const nodesToInclude = [d];
    firstOrderNodeIds.forEach(nodeId => {
        const node = graphData.nodes.find(n => n.id === nodeId);
        if (node) nodesToInclude.push(node);
    });
    
    // Calculate the bounding box for these nodes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodesToInclude.forEach(node => {
        minX = Math.min(minX, node.x);
        minY = Math.min(minY, node.y);
        maxX = Math.max(maxX, node.x);
        maxY = Math.max(maxY, node.y);
    });
    
    // Add some padding
    const padding = 50;
    minX -= padding;
    minY -= padding;
    maxX += padding;
    maxY += padding;
    
    // Calculate the scale and translate to fit this box
    const boxWidth = maxX - minX;
    const boxHeight = maxY - minY;
    const scale = Math.min(width / boxWidth, height / boxHeight) * 0.9;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    
    // First clear any existing highlights
    node.classed("node-highlight", false)
        .classed("node-highlight-first", false)
        .classed("node-highlight-second", false)
        .classed("node-dimmed", false);
    
    link.classed("link-highlight-first", false)
        .classed("link-highlight-second", false)
        .classed("link-dimmed", false);
    
    // Find the current node element
    const currentNode = node.filter(n => n.id === d.id);
    
    // Add highlight class to the current node
    currentNode.classed("node-highlight", true);
    
    // Get second-order connections
    const secondOrderNodeIds = new Set();
    
    // For each first-order node, find its connections
    firstOrderNodeIds.forEach(nodeId => {
        graphData.links.forEach(link => {
            if (link.source.id === nodeId) {
                // Don't include the original node or first-order nodes
                if (link.target.id !== d.id && !firstOrderNodeIds.has(link.target.id)) {
                    secondOrderNodeIds.add(link.target.id);
                }
            } else if (link.target.id === nodeId) {
                // Don't include the original node or first-order nodes
                if (link.source.id !== d.id && !firstOrderNodeIds.has(link.source.id)) {
                    secondOrderNodeIds.add(link.source.id);
                }
            }
        });
    });
    
    // Create sets to track which nodes and links should be highlighted
    const highlightedNodeIds = new Set([d.id, ...firstOrderNodeIds, ...secondOrderNodeIds]);
    const highlightedLinkIndices = new Set();
    
    // Highlight first-order links and nodes
    link.each(function(l, i) {
        const linkElement = d3.select(this);
        if (l.source.id === d.id || l.target.id === d.id) {
            linkElement.classed("link-highlight-first", true);
            highlightedLinkIndices.add(i);
        }
    });
    
    node.each(function(n) {
        const nodeElement = d3.select(this);
        if (firstOrderNodeIds.has(n.id)) {
            nodeElement.classed("node-highlight-first", true);
        }
    });
    
    // Highlight second-order links and nodes
    link.each(function(l, i) {
        const linkElement = d3.select(this);
        // If link connects a first-order node to a second-order node
        if ((firstOrderNodeIds.has(l.source.id) && secondOrderNodeIds.has(l.target.id)) || 
            (firstOrderNodeIds.has(l.target.id) && secondOrderNodeIds.has(l.source.id))) {
            linkElement.classed("link-highlight-second", true);
            highlightedLinkIndices.add(i);
        }
    });
    
    node.each(function(n) {
        const nodeElement = d3.select(this);
        if (secondOrderNodeIds.has(n.id)) {
            nodeElement.classed("node-highlight-second", true);
        }
    });
    
    // Dim all non-highlighted nodes and links
    node.filter(n => !highlightedNodeIds.has(n.id))
        .classed("node-dimmed", true);
    
    link.filter((l, i) => !highlightedLinkIndices.has(i))
        .classed("link-dimmed", true);
    
    // Animate the zoom
    svg.transition()
       .duration(750)
       .call(
            zoom.transform,
            d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(scale)
                .translate(-centerX, -centerY)
        )
       .on("end", function() {
            // Reorder elements for proper rendering AFTER the animation completes
            reorderHighlightedElements(currentNode);
            
            // Show tooltip if the node's title is truncated
            if (d.isTruncated) {
                // Get the final transform after animation
                const finalTransform = d3.zoomTransform(svg.node());
                showTooltip(d, finalTransform);
            }
       });
    
    // Show tooltip if the node's title is truncated
    if (d.isTruncated) {
        // Note: We don't show the tooltip here anymore
        // It will be shown in the "end" event of the zoom transition
        // This ensures the tooltip is positioned correctly after the zoom animation
    }
}

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
    .attr("r", d => {
        // Increase the relative size difference between nodes
        // Store the radius on the data object for later use
        d.radius = d.connections ? 10 + Math.pow(d.connections, 0.8) * 2 : 10;
        return d.radius;
    })
    .attr("fill", d => getNodeColor(d))
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .on("click", function(event, d) {
        // Prevent event from propagating to potential parent elements
        event.stopPropagation();
        
        // Hide any existing tooltips immediately without transition
        hideTooltipImmediately();
        
        // If this node is already highlighted, clear the highlight
        if (highlightedNode === d) {
            clearHighlightAndResetZoom();
        } else {
            // Otherwise, highlight and zoom to this node
            highlightAndZoomToNode(d);
        }
    })
    .on("dblclick", function(event, d) {
        // Prevent event from propagating and prevent default behavior
        event.stopPropagation();
        event.preventDefault();
        
        // Open the wiki document in a new window
        if (d.urlId) {
            window.open(`https://lore.dungeon.church/doc/-${d.urlId}`, '_blank');
        }
    })
    .on("contextmenu", function(event) {
        // Prevent the default context menu
        event.preventDefault();
        
        // Clear highlight state and reset zoom
        clearHighlightAndResetZoom();
    })
    .on("mouseover", function(event, d) {
        // If we already have a highlighted node, don't do anything on mouseover
        // unless it's the highlighted node itself (to ensure tooltip shows correctly)
        if (highlightedNode && highlightedNode !== d) return;
        
        // Get the current node element
        const currentNode = d3.select(this.parentNode);
        
        // If no node is highlighted, add temporary highlight class
        if (!highlightedNode) {
            // Add highlight class to the current node
            currentNode.classed("node-highlight", true);
            
            // Get first-order connections
            const firstOrderLinks = graphData.links.filter(link => 
                link.source.id === d.id || link.target.id === d.id
            );
            
            const firstOrderNodeIds = new Set();
            firstOrderLinks.forEach(link => {
                const connectedId = link.source.id === d.id ? link.target.id : link.source.id;
                firstOrderNodeIds.add(connectedId);
            });
            
            // Get second-order connections
            const secondOrderNodeIds = new Set();
            
            // For each first-order node, find its connections
            firstOrderNodeIds.forEach(nodeId => {
                graphData.links.forEach(link => {
                    if (link.source.id === nodeId) {
                        // Don't include the original node or first-order nodes
                        if (link.target.id !== d.id && !firstOrderNodeIds.has(link.target.id)) {
                            secondOrderNodeIds.add(link.target.id);
                        }
                    } else if (link.target.id === nodeId) {
                        // Don't include the original node or first-order nodes
                        if (link.source.id !== d.id && !firstOrderNodeIds.has(link.source.id)) {
                            secondOrderNodeIds.add(link.source.id);
                        }
                    }
                });
            });
            
            // Create sets to track which nodes and links should be highlighted
            const highlightedNodeIds = new Set([d.id, ...firstOrderNodeIds, ...secondOrderNodeIds]);
            const highlightedLinkIndices = new Set();
            
            // Highlight first-order links and nodes
            link.each(function(l, i) {
                const linkElement = d3.select(this);
                if (l.source.id === d.id || l.target.id === d.id) {
                    linkElement.classed("link-highlight-first", true);
                    highlightedLinkIndices.add(i);
                }
            });
            
            node.each(function(n) {
                const nodeElement = d3.select(this);
                if (firstOrderNodeIds.has(n.id)) {
                    nodeElement.classed("node-highlight-first", true);
                }
            });
            
            // Highlight second-order links and nodes
            link.each(function(l, i) {
                const linkElement = d3.select(this);
                // If link connects a first-order node to a second-order node
                if ((firstOrderNodeIds.has(l.source.id) && secondOrderNodeIds.has(l.target.id)) || 
                    (firstOrderNodeIds.has(l.target.id) && secondOrderNodeIds.has(l.source.id))) {
                    linkElement.classed("link-highlight-second", true);
                    highlightedLinkIndices.add(i);
                }
            });
            
            node.each(function(n) {
                const nodeElement = d3.select(this);
                if (secondOrderNodeIds.has(n.id)) {
                    nodeElement.classed("node-highlight-second", true);
                }
            });
            
            // Dim all non-highlighted nodes and links
            node.each(function(n) {
                const nodeElement = d3.select(this);
                if (!highlightedNodeIds.has(n.id)) {
                    nodeElement.classed("node-dimmed", true);
                }
            });
            
            link.each(function(l, i) {
                const linkElement = d3.select(this);
                if (!highlightedLinkIndices.has(i)) {
                    linkElement.classed("link-dimmed", true);
                }
            });
            // Reorder elements to bring highlighted network to front
            reorderHighlightedElements(currentNode);
        }
        
        // Show tooltip if the node's title is truncated
        if (d.isTruncated) {
            // Get current transform
            const transform = d3.zoomTransform(svg.node());
            showTooltip(d, transform);
        }
    })
    .on("mouseout", function(event, d) {
        // If we have a highlighted node, don't clear highlights on mouseout
        // unless it's the highlighted node itself (to ensure proper tooltip behavior)
        if (highlightedNode && highlightedNode !== d) return;
        
        if (!highlightedNode) {
            // Remove all highlight and dimmed classes
            node.classed("node-highlight", false)
                .classed("node-highlight-first", false)
                .classed("node-highlight-second", false)
                .classed("node-dimmed", false);
            
            link.classed("link-highlight-first", false)
                .classed("link-highlight-second", false)
                .classed("link-dimmed", false);
                
            // Reset the rendering order
            node.order();
            link.order();
        }
            
        // Hide tooltip only if we're not in highlight mode or if this is the highlighted node
        if (!highlightedNode || highlightedNode === d) {
            hideTooltip();
        }
    });

// Add labels to nodes - move inside the circle with improved centering
node.append("text")
    .attr("text-anchor", "middle") // Center text horizontally
    .attr("dominant-baseline", "central") // Center text vertically
    .each(function(d) {
        const text = d3.select(this);
        const radius = d.radius;
        const title = d.title || "Node"; // Ensure there's always some text
        
        // Function to calculate available width at a given vertical offset in a circle
        function getAvailableWidthAtOffset(radius, yOffset) {
            // Pythagoras: in a circle, width at offset y from center is 2*sqrt(r²-y²)
            return 2 * Math.sqrt(Math.max(0, radius * radius - yOffset * yOffset));
        }
        
        // Function to fit text in the circle
        function fitTextInCircle(text, title, radius) {
            text.selectAll("*").remove(); // Clear any existing content
            
            // Constants for text fitting
            const minFontSize = 6;
            const maxFontSize = Math.min(radius * 0.6, 14);
            const maxLines = Math.min(5, Math.max(1, Math.floor(radius / 6)));
            const padding = 2; // Padding inside the circle
            
            // Start with maximum font size and single line
            let fontSize = maxFontSize;
            let lineCount = 1;
            let shouldTruncate = false;
            
            // Try different configurations until text fits
            while (fontSize >= minFontSize) {
                // Set font size for measurement
                text.style("font-size", fontSize + "px");
                
                // Calculate line height based on font size
                const lineHeight = fontSize * 1.2;
                
                // Calculate total height for current line count
                const totalTextHeight = lineHeight * lineCount;
                
                // Check if total height exceeds available height with padding
                if (totalTextHeight > (radius * 2 - padding * 2)) {
                    // If we can't reduce font size further, we need to truncate
                    if (fontSize <= minFontSize) {
                        shouldTruncate = true;
                        break;
                    }
                    
                    // Try smaller font size
                    fontSize -= 0.5;
                    continue;
                }
                
                // Split text into words
                const words = title.split(/\s+/);
                
                // Try to fit text with current font size and line count
                const lines = [];
                let currentLine = [];
                let success = true;
                
                // Create a temporary text element to measure text width
                const tempText = text.append("tspan").style("opacity", 0);
                
                // Calculate vertical positions for lines
                const verticalPositions = [];
                for (let i = 0; i < lineCount; i++) {
                    // Calculate y-offset from center for this line
                    const yOffset = (i - (lineCount - 1) / 2) * lineHeight;
                    verticalPositions.push(yOffset);
                    
                    // Calculate available width at this vertical position
                    const availableWidth = getAvailableWidthAtOffset(radius - padding, yOffset) - padding * 2;
                    
                    // Try to fit words on this line
                    while (words.length > 0) {
                        currentLine.push(words[0]);
                        tempText.text(currentLine.join(" "));
                        
                        if (tempText.node().getComputedTextLength() > availableWidth) {
                            // If even a single word doesn't fit on an empty line
                            if (currentLine.length === 1) {
                                // If we can add more lines, try that
                                if (lineCount < maxLines) {
                                    success = false;
                                    break;
                                } else if (fontSize > minFontSize) {
                                    // Try smaller font
                                    success = false;
                                    break;
                                } else {
                                    // We need to truncate this word
                                    let truncatedWord = currentLine[0];
                                    while (truncatedWord.length > 3) {
                                        truncatedWord = truncatedWord.slice(0, -1);
                                        tempText.text(truncatedWord + "...");
                                        if (tempText.node().getComputedTextLength() <= availableWidth) {
                                            currentLine[0] = truncatedWord + "...";
                                            break;
                                        }
                                    }
                                }
                            } else {
                                // Remove the last word that didn't fit
                                currentLine.pop();
                            }
                            
                            // Add current line to lines array
                            lines.push(currentLine.join(" "));
                            currentLine = [];
                            break;
                        }
                        
                        // Word fits, remove it from words array
                        words.shift();
                        
                        // If we've used all words, add the current line
                        if (words.length === 0) {
                            lines.push(currentLine.join(" "));
                            break;
                        }
                    }
                    
                    // If we couldn't fit text with current configuration
                    if (!success) break;
                    
                    // If we've used all words, we're done
                    if (words.length === 0) break;
                }
                
                // Remove temporary element
                tempText.remove();
                
                // If we have remaining words, we need more lines or smaller font
                if (words.length > 0) {
                    if (lineCount < maxLines) {
                        // Try more lines
                        lineCount++;
                    } else if (fontSize > minFontSize) {
                        // Try smaller font
                        fontSize -= 0.5;
                    } else {
                        // We need to truncate
                        shouldTruncate = true;
                        break;
                    }
                    continue;
                }
                
                // If we've successfully fit all text, create the tspans
                if (success) {
                    // Create a container group for better positioning
                    const lineCount = lines.length;
                    const totalHeight = lineHeight * lineCount;
                    
                    // Create tspans for each line with precise positioning
                    lines.forEach((line, i) => {
                        // Calculate vertical position
                        // For single line, y=0 (center)
                        // For multiple lines, distribute evenly around center
                        const yPos = lineCount === 1 ? 0 : 
                                    (i - (lineCount - 1) / 2) * lineHeight;
                        
                        text.append("tspan")
                            .attr("x", 0)
                            .attr("y", yPos)
                            .attr("dy", 0) // No additional vertical offset
                            .text(line);
                    });
                    
                    // Mark node as not truncated
                    d.isTruncated = false;
                    
                    return true;
                }
            }
            
            // If we need to truncate, create a single line with ellipsis
            if (shouldTruncate) {
                text.style("font-size", minFontSize + "px");
                
                // Calculate available width at center
                const availableWidth = getAvailableWidthAtOffset(radius - padding, 0) - padding * 2;
                
                // Ensure we show at least the first few characters
                let truncatedText = title;
                const tempText = text.append("tspan").style("opacity", 0);
                
                // If title is empty or undefined, use a default
                if (!title || title.trim() === "") {
                    truncatedText = "Node";
                } else {
                    tempText.text(truncatedText);
                    while (tempText.node().getComputedTextLength() > availableWidth && truncatedText.length > 3) {
                        truncatedText = truncatedText.slice(0, -1);
                        tempText.text(truncatedText + "...");
                    }
                    
                    // If we're down to just one character, don't add ellipsis
                    if (truncatedText.length === 1) {
                        tempText.text(truncatedText);
                    }
                }
                
                tempText.remove();
                
                // Add truncated text
                text.append("tspan")
                    .attr("x", 0)
                    .attr("y", 0)
                    .text(truncatedText.length === 1 ? truncatedText : truncatedText + "...");
                
                // Mark node as truncated
                d.isTruncated = true;
            }
            
            return true;
        }
        
        // Fit the text in the circle
        fitTextInCircle(text, title, radius);
        
        // Store the font size on the data object
        d.fontSize = parseFloat(text.style("font-size"));
        
        // Ensure text is visible by checking if any tspans were created
        if (text.selectAll("tspan").size() === 0) {
            // If no tspans were created, add a default one
            text.append("tspan")
                .attr("x", 0)
                .attr("y", 0)
                .text(title.substring(0, 1)); // Just show first character without ellipsis
                
            // Mark node as truncated
            d.isTruncated = true;
        }
    })
    .style("opacity", 0.9)
    .style("pointer-events", "none"); // Ensure text doesn't interfere with mouse events

// Update positions on each tick
simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
    
    node
        .attr("transform", d => `translate(${d.x},${d.y})`);
});

// Helper functions
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function getNodeColor(node) {
    // Use the dynamically generated collection colors if available
    if (typeof collectionColors !== 'undefined' && collectionColors[node.collectionId]) {
        return collectionColors[node.collectionId];
    }
    
    // Fallback to hardcoded colors if collection colors are not available
    const collections = {
        "13b87098-500c-490d-ae46-01356387fe88": "#ff7f0e", // Adventures
        "7275a3d8-27da-4f63-ac39-a9bc9a1ec6d7": "#1f77b4", // Spells
        // Add more collections as needed
    };
    
    return collections[node.collectionId] || "#69b3a2";
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
}

// Search functionality
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");

searchInput.addEventListener("input", function() {
    const query = this.value.toLowerCase();
    
    if (query.length < 2) {
        searchResults.style.display = "none";
        return;
    }
    
    // Filter nodes based on search query
    const matchingNodes = graphData.nodes.filter(node => 
        node.title.toLowerCase().includes(query)
    ).slice(0, 10); // Limit to 10 results
    
    // Display results
    if (matchingNodes.length > 0) {
        searchResults.innerHTML = "";
        matchingNodes.forEach(node => {
            const resultItem = document.createElement("div");
            resultItem.className = "search-result";
            resultItem.textContent = node.title;
            resultItem.addEventListener("click", function() {
                // Use the shared function to highlight and zoom to the node
                highlightAndZoomToNode(node);
                
                // Clear search
                searchInput.value = "";
                searchResults.style.display = "none";
            });
            searchResults.appendChild(resultItem);
        });
        searchResults.style.display = "block";
    } else {
        searchResults.innerHTML = "<div class='search-result'>No results found</div>";
        searchResults.style.display = "block";
    }
});

// Close search results when clicking outside
document.addEventListener("click", function(event) {
    if (event.target !== searchInput && !searchResults.contains(event.target)) {
        searchResults.style.display = "none";
    }
});

// Function to handle resize events
function handleResize() {
    // Get new dimensions
    const newDimensions = getContainerDimensions();
    width = newDimensions.width;
    height = newDimensions.height;
    
    // Update SVG dimensions
    svg.attr("width", width)
       .attr("height", height);
    
    // Recenter if needed
    if (!highlightedNode) {
        svg.transition().duration(300).call(
            zoom.transform,
            d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5)
        );
    }
    
    // Update tooltip position if visible
    if (parseFloat(tooltipTruncated.style("opacity")) > 0 && highlightedNode) {
        updateTooltipPosition(highlightedNode);
    }
}

// Set up resize observer for container
if (typeof ResizeObserver !== 'undefined') {
    const resizeObserver = new ResizeObserver(entries => {
        // We only observe one element, so we can just use the first entry
        handleResize();
    });
    
    // Start observing the visualization container
    resizeObserver.observe(document.getElementById('visualization'));
} else {
    // Fallback to window resize event for older browsers
    window.addEventListener('resize', handleResize);
}

// Handle iframe resize messages from parent
window.addEventListener('message', function(event) {
    // Check if the message is a resize notification
    if (event.data && event.data.type === 'resize') {
        // Force a resize calculation
        handleResize();
    }
});
