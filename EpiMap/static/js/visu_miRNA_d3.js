function getNodeColor(node, neighbors) {
    if (Array.isArray(neighbors) && neighbors.indexOf(node.id) > -1) {
        return node.level === 1 ? 'blue' : 'green'
    }
    return node.level === 1 ? 'red' : 'gray';
}

function getTextColor(node, neighbors) {
    return Array.isArray(neighbors) && neighbors.indexOf(node.id) > -1 ? 'green' : 'black'
}

function getLinkColor(node, link) {
    return Array.isArray(link) && isNeighborLink(node, link) > -1 ? 'green' : '#e5e5e5'
}

function getNeighbors(node) {
    return links.reduce((neighbors, link) => {
        if (link.target.id === node.id) {
            neighbors.push(link.source.id)
        } else if (link.source.id === node.id) {
            neighbors.push(link.target.id)
        }
        return neighbors
    }, [node.id])
}

function isNeighborLink(node, link) {
    return link.target.id === node.id || link.source.id === node.id
}

function selectNode(selectedNode) {
    var neighbors = getNeighbors(selectedNode);
    nodeElements.attr('fill', node => getNodeColor(node, neighbors));
    textElements.attr('fill', node => getTextColor(node, neighbors));
    linkElements.attr('stroke', link => getLinkColor(selectedNode, link));
}

function mouseOut() {
    nodeElements.attr('fill', node => getNodeColor(node));
    textElements.attr('fill', node => getTextColor(node));
    linkElements.attr('stroke', link => getLinkColor(link));
}

// define container
//var width = window.innerWidth, height = window.innerHeight/2;
var margin = {top: 30, right: 10, bottom: 30, left: 10}
var width = parseInt(d3.select('#visualization').style('width')), height = window.innerHeight / 2;
var svg = d3.select('svg')
    .attr('width', width - margin.left - margin.right)
    .attr('height', height)
    // call d3 zoom event, must append a g tag
    .call(d3.zoom().on("zoom", function () {
        svg.attr("transform", d3.event.transform)
    }))
    .append('g');

// define simulator
var simulation = d3.forceSimulation()
// push nodes apart to space them out
    .force('charge', d3.forceManyBody().strength(-20))
    // draw them around the centre of the space
    .force('center', d3.forceCenter(width / 2, height / 2))
    // pull nodes together based on the links between them
    .force('link', d3.forceLink().id(link => link.id).strength(link => link.strength))
    // add some collision detection so they don't overlap
    .force("collide", d3.forceCollide().radius(20))
    .force('x', d3.forceX(width / 2).strength(0.01))
    .force('y', d3.forceY(height / 2).strength(0.01));


// define nodes, texts, links and drag&drop
var nodeElements = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('r', 5)
    .attr('fill', getNodeColor)
    // mouse event
    .on('click', selectNode)
    .on('mouseover', selectNode)
    .on('mouseout', mouseOut);
var textElements = svg.append('g')
    .attr('class', 'texts')
    .selectAll('text')
    .data(nodes)
    .enter().append('text')
    .text(node => node.label)
    .attr('font-size', 15)
    .attr('dx', 15)
    .attr('dy', 4);
var linkElements = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('stroke-width', 1)
    .attr('stroke', 'rgba(50, 50, 50, 0.2)');

var dragDrop = d3.drag()
    .on('start', node => {
        node.fx = node.x;
        node.fy = node.y;
    })
    .on('drag', node => {
        simulation.alphaTarget(0.7).restart();
        node.fx = d3.event.x;
        node.fy = d3.event.y;
    })
    .on('end', node => {
        if (!d3.event.active) {
            simulation.alphaTarget(0);
        }
        node.fx = null;
        node.fy = null;
    });
nodeElements.call(dragDrop);

// setup
simulation.nodes(nodes).on('tick', () => {
    nodeElements
        .attr('cx', node => node.x)
        .attr('cy', node => node.y);
    textElements
        .attr('x', node => node.x)
        .attr('y', node => node.y);
    linkElements
        .attr('x1', link => link.source.x)
        .attr('y1', link => link.source.y)
        .attr('x2', link => link.target.x)
        .attr('y2', link => link.target.y);
});
simulation.force('link').links(links)