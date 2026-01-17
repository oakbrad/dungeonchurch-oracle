// This file will be populated with graph data by create_viz.py
// The graphData variable will be defined at the top of this file

// View mode: 'connection' or 'alignment'
let currentViewMode = 'connection';

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

// Helper function to calculate node connections (first and second order)
// Returns { firstOrderNodeIds, secondOrderNodeIds, firstOrderLinks }
function calculateNodeConnections(nodeId) {
    // Get first-order connections
    const firstOrderLinks = graphData.links.filter(link =>
        link.source.id === nodeId || link.target.id === nodeId
    );

    const firstOrderNodeIds = new Set();
    firstOrderLinks.forEach(link => {
        const connectedId = link.source.id === nodeId ? link.target.id : link.source.id;
        firstOrderNodeIds.add(connectedId);
    });

    // Get second-order connections
    const secondOrderNodeIds = new Set();
    firstOrderNodeIds.forEach(firstNodeId => {
        graphData.links.forEach(link => {
            if (link.source.id === firstNodeId) {
                if (link.target.id !== nodeId && !firstOrderNodeIds.has(link.target.id)) {
                    secondOrderNodeIds.add(link.target.id);
                }
            } else if (link.target.id === firstNodeId) {
                if (link.source.id !== nodeId && !firstOrderNodeIds.has(link.source.id)) {
                    secondOrderNodeIds.add(link.source.id);
                }
            }
        });
    });

    return { firstOrderNodeIds, secondOrderNodeIds, firstOrderLinks };
}

// Helper function to clear all highlight classes from nodes and links
function clearAllHighlights() {
    node.classed("node-highlight", false)
        .classed("node-highlight-first", false)
        .classed("node-highlight-second", false)
        .classed("node-dimmed", false);

    link.classed("link-highlight-first", false)
        .classed("link-highlight-second", false)
        .classed("link-dimmed", false);
}

// Helper function to apply highlight classes based on connection data
function applyHighlightClasses(nodeId, connections) {
    const { firstOrderNodeIds, secondOrderNodeIds } = connections;
    const highlightedNodeIds = new Set([nodeId, ...firstOrderNodeIds, ...secondOrderNodeIds]);
    const highlightedLinkIndices = new Set();

    // Apply first-order link highlighting
    link.classed("link-highlight-first", (l, i) => {
        const isFirst = l.source.id === nodeId || l.target.id === nodeId;
        if (isFirst) highlightedLinkIndices.add(i);
        return isFirst;
    });

    // Apply first-order node highlighting
    node.classed("node-highlight-first", n => firstOrderNodeIds.has(n.id));

    // Apply second-order link highlighting
    link.classed("link-highlight-second", (l, i) => {
        const isSecond = (firstOrderNodeIds.has(l.source.id) && secondOrderNodeIds.has(l.target.id)) ||
                        (firstOrderNodeIds.has(l.target.id) && secondOrderNodeIds.has(l.source.id));
        if (isSecond) highlightedLinkIndices.add(i);
        return isSecond;
    });

    // Apply second-order node highlighting
    node.classed("node-highlight-second", n => secondOrderNodeIds.has(n.id));

    // Dim non-highlighted elements
    node.classed("node-dimmed", n => !highlightedNodeIds.has(n.id));
    link.classed("link-dimmed", (l, i) => !highlightedLinkIndices.has(i));

    return highlightedLinkIndices;
}

// Function to clear highlight state and reset zoom
function clearHighlightAndResetZoom() {
    if (highlightedNode) {
        // Remove all highlight and dimmed classes using helper
        clearAllHighlights();

        // Hide tooltip immediately without transition
        hideTooltipImmediately();

        // Reset the highlighted node tracker
        highlightedNode = null;

        // If in alignment mode, re-apply alignment default styles
        if (currentViewMode === 'alignment') {
            applyAlignmentDefaultStyles();
            // Reset zoom to alignment view center
            const scale = Math.min(width, height) / (alignmentGridSize * 0.8 * 2.5);
            svg.interrupt().transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(width / 2, height / 2).scale(scale)
            );
        } else {
            // Reset zoom to default center view
            svg.interrupt().transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5)
            );
        }

        // Reset the rendering order
        node.order();
        link.order();
    }
}

// Function to highlight and zoom to a node
function highlightAndZoomToNode(d) {
    // Hide any existing tooltips immediately without transition
    hideTooltipImmediately();

    // If in alignment mode, clear the default alignment styles first
    if (currentViewMode === 'alignment') {
        clearAlignmentDefaultStyles();
    }

    // Set this node as the highlighted node
    highlightedNode = d;

    // Calculate connections using shared helper
    const connections = calculateNodeConnections(d.id);
    const { firstOrderNodeIds } = connections;

    // Get all nodes that need to be included in the view for zoom calculation
    const nodesToInclude = [d];
    firstOrderNodeIds.forEach(nodeId => {
        const n = nodeMap.get(nodeId);
        if (n) nodesToInclude.push(n);
    });

    // Calculate the bounding box for these nodes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodesToInclude.forEach(n => {
        minX = Math.min(minX, n.x);
        minY = Math.min(minY, n.y);
        maxX = Math.max(maxX, n.x);
        maxY = Math.max(maxY, n.y);
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

    // Clear existing highlights and apply new ones
    clearAllHighlights();

    // Find the current node element and highlight it
    const currentNode = node.filter(n => n.id === d.id);
    currentNode.classed("node-highlight", true);

    // Apply connection highlighting
    applyHighlightClasses(d.id, connections);

    // Animate the zoom
    svg.interrupt().transition()
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
            node.lower();
            link.lower();

            // Raise elements in order of importance
            link.filter(".link-highlight-second").raise();
            node.filter(".node-highlight-second").raise();
            link.filter(".link-highlight-first").raise();
            node.filter(".node-highlight-first").raise();
            currentNode.raise();

            // Show tooltip if the node's title is truncated
            if (d.isTruncated) {
                const finalTransform = d3.zoomTransform(svg.node());
                showTooltip(d, finalTransform);
            }
       });
}

// Alignment grid dimensions (in simulation coordinates)
const alignmentGridSize = 800;

// Create alignment grid background (hidden by default)
const alignmentGrid = g.append("g")
    .attr("class", "alignment-grid")
    .style("display", "none");

// Draw 3x3 alignment grid
const gridLabels = [
    { x: -1, y: 1, label: "Lawful Good", abbr: "LG" },
    { x: 0, y: 1, label: "Neutral Good", abbr: "NG" },
    { x: 1, y: 1, label: "Chaotic Good", abbr: "CG" },
    { x: -1, y: 0, label: "Lawful Neutral", abbr: "LN" },
    { x: 0, y: 0, label: "True Neutral", abbr: "N" },
    { x: 1, y: 0, label: "Chaotic Neutral", abbr: "CN" },
    { x: -1, y: -1, label: "Lawful Evil", abbr: "LE" },
    { x: 0, y: -1, label: "Neutral Evil", abbr: "NE" },
    { x: 1, y: -1, label: "Chaotic Evil", abbr: "CE" }
];

// Grid cell size
const cellSize = alignmentGridSize / 3;

// Draw quadrant labels only (no background rectangles)
gridLabels.forEach(cell => {
    const cellX = cell.x * cellSize;
    const cellY = -cell.y * cellSize; // Invert Y so good is at top

    // Draw cell label
    alignmentGrid.append("text")
        .attr("x", cellX)
        .attr("y", cellY)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("class", "alignment-label")
        .attr("fill", "#555")
        .attr("font-size", "28px")
        .attr("font-family", "'DungeonChurch', 'Courier New', monospace")
        .text(cell.abbr);
});

// Axis extends well beyond the grid for prominence
const axisExtent = alignmentGridSize * 0.8;

// Draw prominent red cross axis lines
alignmentGrid.append("line")
    .attr("x1", -axisExtent)
    .attr("y1", 0)
    .attr("x2", axisExtent)
    .attr("y2", 0)
    .attr("stroke", "#cc3333")
    .attr("stroke-width", 3)
    .attr("opacity", 0.8);

alignmentGrid.append("line")
    .attr("x1", 0)
    .attr("y1", -axisExtent)
    .attr("x2", 0)
    .attr("y2", axisExtent)
    .attr("stroke", "#cc3333")
    .attr("stroke-width", 3)
    .attr("opacity", 0.8);

// Draw axis labels at ends of cross
alignmentGrid.append("text")
    .attr("x", 0)
    .attr("y", -axisExtent - 25)
    .attr("text-anchor", "middle")
    .attr("fill", "#cc9966")
    .attr("font-size", "32px")
    .attr("font-family", "'DungeonChurch', 'Courier New', monospace")
    .text("GOOD");

alignmentGrid.append("text")
    .attr("x", 0)
    .attr("y", axisExtent + 40)
    .attr("text-anchor", "middle")
    .attr("fill", "#cc9966")
    .attr("font-size", "32px")
    .attr("font-family", "'DungeonChurch', 'Courier New', monospace")
    .text("EVIL");

alignmentGrid.append("text")
    .attr("x", -axisExtent - 25)
    .attr("y", 0)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("fill", "#cc9966")
    .attr("font-size", "32px")
    .attr("font-family", "'DungeonChurch', 'Courier New', monospace")
    .attr("transform", `rotate(-90, ${-axisExtent - 25}, 0)`)
    .text("LAWFUL");

alignmentGrid.append("text")
    .attr("x", axisExtent + 25)
    .attr("y", 0)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("fill", "#cc9966")
    .attr("font-size", "32px")
    .attr("font-family", "'DungeonChurch', 'Courier New', monospace")
    .attr("transform", `rotate(90, ${axisExtent + 25}, 0)`)
    .text("CHAOTIC");

// Create the force simulation
const simulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.links)
        .id(d => d.id)
        .distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(0, 0))
    .force("collide", d3.forceCollide(30));

// Store original force configuration for connection mode
const connectionForces = {
    link: simulation.force("link"),
    charge: simulation.force("charge"),
    center: simulation.force("center"),
    collide: simulation.force("collide")
};

// Function to switch to alignment view mode
function switchToAlignmentMode() {
    currentViewMode = 'alignment';

    // Show alignment grid
    alignmentGrid.style("display", "block");

    // Update forces for alignment positioning
    simulation
        .force("link", d3.forceLink(graphData.links)
            .id(d => d.id)
            .distance(80)
            .strength(0.05)) // Very weak links in alignment mode
        .force("charge", d3.forceManyBody()
            .strength(-200)) // Stronger repulsion to spread nodes out
        .force("center", null) // Remove center force
        .force("alignX", d3.forceX(d => {
            if (d.alignment && d.alignment.final) {
                // law_chaos: -1 (chaotic/right) to 1 (lawful/left)
                // Invert so chaotic is right, lawful is left
                return -d.alignment.final.law_chaos * (alignmentGridSize / 2);
            }
            return 0;
        }).strength(d => d.alignment ? d.alignment.confidence * 0.3 : 0.1))
        .force("alignY", d3.forceY(d => {
            if (d.alignment && d.alignment.final) {
                // good_evil: -1 (evil/bottom) to 1 (good/top)
                // Invert Y so good is at top
                return -d.alignment.final.good_evil * (alignmentGridSize / 2);
            }
            return 0;
        }).strength(d => d.alignment ? d.alignment.confidence * 0.3 : 0.1))
        .force("collide", d3.forceCollide(25));

    // Get alignment-eligible collection IDs from graph data
    const alignmentCollectionIds = new Set(graphData.alignmentCollectionIds || []);

    // Helper to check if node is alignment-eligible (Characters, NPCs, Organizations)
    const isAlignmentNode = d => alignmentCollectionIds.has(d.collectionId);

    // Hide non-alignment nodes completely, show alignment nodes
    node.interrupt().transition()
        .duration(500)
        .style("display", d => isAlignmentNode(d) ? "block" : "none");

    // Apply alignment-specific CSS classes based on collection type
    applyAlignmentDefaultStyles();

    // Hide links that connect to non-alignment nodes
    link.interrupt().transition()
        .duration(500)
        .style("display", d => {
            const sourceNode = typeof d.source === 'object' ? d.source : nodeMap.get(d.source);
            const targetNode = typeof d.target === 'object' ? d.target : nodeMap.get(d.target);
            const sourceOk = sourceNode && alignmentCollectionIds.has(sourceNode.collectionId);
            const targetOk = targetNode && alignmentCollectionIds.has(targetNode.collectionId);
            return (sourceOk && targetOk) ? "block" : "none";
        });

    // Restart simulation
    simulation.alpha(1).restart();

    // Zoom to center on the alignment axis
    // Scale to fit the axis extent within the viewport
    const scale = Math.min(width, height) / (axisExtent * 2.5);
    svg.interrupt().transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(scale));

    // Update toggle button - show circle-nodes icon for switching back to connection view
    const toggleBtn = document.getElementById("view-toggle");
    toggleBtn.innerHTML = '<i class="fa-solid fa-circle-nodes"></i>';
    toggleBtn.title = "Switch to Connection View";
    toggleBtn.classList.add("active");
}

// Collection type IDs for alignment styling
const CHARACTERS_COLLECTION = '184c6e39-ef59-49b4-89d8-302d6abae3cf';
const ORGANIZATIONS_COLLECTION = '28015ad0-50f5-4495-a6c5-2415436a3d40';
const NPCS_COLLECTION = '098323c3-c9a2-45f4-ab12-ff8b759c5be7';

// Function to apply alignment default styles (called when entering alignment mode or clearing highlight)
function applyAlignmentDefaultStyles() {
    node.classed("alignment-character", d => d.collectionId === CHARACTERS_COLLECTION)
        .classed("alignment-org", d => d.collectionId === ORGANIZATIONS_COLLECTION)
        .classed("alignment-npc", d => d.collectionId === NPCS_COLLECTION);
}

// Function to clear alignment default styles
function clearAlignmentDefaultStyles() {
    node.classed("alignment-character", false)
        .classed("alignment-org", false)
        .classed("alignment-npc", false);
}

// Function to switch to connection view mode
function switchToConnectionMode() {
    currentViewMode = 'connection';

    // Hide alignment grid
    alignmentGrid.style("display", "none");

    // Clear alignment-specific CSS classes
    clearAlignmentDefaultStyles();

    // Restore original forces
    simulation
        .force("link", d3.forceLink(graphData.links)
            .id(d => d.id)
            .distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(0, 0))
        .force("alignX", null)
        .force("alignY", null)
        .force("collide", d3.forceCollide(30));

    // Show all nodes again
    node.interrupt().transition()
        .duration(500)
        .style("display", "block");

    // Show all links again
    link.interrupt().transition()
        .duration(500)
        .style("display", "block");

    // Restart simulation
    simulation.alpha(1).restart();

    // Reset zoom to default view
    svg.interrupt().transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(0.5));

    // Update toggle button - show scale-balanced icon for switching to alignment view
    const toggleBtn = document.getElementById("view-toggle");
    toggleBtn.innerHTML = '<i class="fa-solid fa-scale-balanced"></i>';
    toggleBtn.title = "Switch to Alignment View";
    toggleBtn.classList.remove("active");
}

// Function to toggle view mode
function toggleViewMode() {
    if (currentViewMode === 'connection') {
        switchToAlignmentMode();
    } else {
        switchToConnectionMode();
    }
}

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
            // If in alignment mode, clear the default alignment styles first
            if (currentViewMode === 'alignment') {
                clearAlignmentDefaultStyles();
            }

            // Add highlight class to the current node
            currentNode.classed("node-highlight", true);

            // Calculate and apply connection highlighting using shared helpers
            const connections = calculateNodeConnections(d.id);
            applyHighlightClasses(d.id, connections);
        }

        // Show tooltip if the node's title is truncated
        if (d.isTruncated) {
            const transform = d3.zoomTransform(svg.node());
            showTooltip(d, transform);
        }
    })
    .on("mouseout", function(event, d) {
        // If we have a highlighted node, don't clear highlights on mouseout
        // unless it's the highlighted node itself (to ensure proper tooltip behavior)
        if (highlightedNode && highlightedNode !== d) return;

        if (!highlightedNode) {
            // Remove all highlight and dimmed classes using helper
            clearAllHighlights();

            // If in alignment mode, re-apply default alignment styles
            if (currentViewMode === 'alignment') {
                applyAlignmentDefaultStyles();
            }

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
    };

    return collections[node.collectionId] || "#69b3a2";
}

// Search functionality
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");

// Debounce helper function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced search handler (200ms delay)
const handleSearch = debounce(function(query) {
    if (query.length < 2) {
        searchResults.style.display = "none";
        return;
    }

    // Filter nodes based on search query
    const matchingNodes = graphData.nodes.filter(node =>
        node.title.toLowerCase().includes(query)
    ).slice(0, 10); // Limit to 10 results

    // Build results using document fragment for better performance
    const fragment = document.createDocumentFragment();

    if (matchingNodes.length > 0) {
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
            fragment.appendChild(resultItem);
        });
    } else {
        const noResults = document.createElement("div");
        noResults.className = "search-result";
        noResults.textContent = "No results found";
        fragment.appendChild(noResults);
    }

    searchResults.innerHTML = "";
    searchResults.appendChild(fragment);
    searchResults.style.display = "block";
}, 200);

searchInput.addEventListener("input", function() {
    handleSearch(this.value.toLowerCase());
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
