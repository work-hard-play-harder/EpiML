function getNodeColor(node, neighbors) {
    /*
    if (Array.isArray(neighbors) && neighbors.indexOf(node.id) > -1) {
        return 'green'
    }*/
    return color(node.group); // use color schemeCategory10
    //return node.fill; // directly assign fill color
}

function getNodeType(node) {
    if (node.shape === 'circle') {
        return d3.symbolCircle;
    }
    if (node.shape === 'cross') {
        return d3.symbolCross;
    }
    if (node.shape === 'diamond') {
        return d3.symbolDiamond;
    }
    if (node.shape === 'square') {
        return d3.symbolSquare;
    }
    if (node.shape === 'star') {
        return d3.symbolStar;
    }
    if (node.shape === 'triangle') {
        return d3.symbolTriangle;
    }
    if (node.shape === 'wye') {
        return d3.symbolWye;
    }
}

function getNodeSize(node) {
    return node.size;
}

function getTextColor(node, neighbors) {
    return Array.isArray(neighbors) && neighbors.indexOf(node.id) > -1 ? 'green' : 'black'
}

function getLinkColor(node, link) {
    return isNeighborLink(node, link) ? 'green' : 'rgba(50, 50, 50, 0.2)'
}

function getLegendType(legend) {
    if (legend.shape === 'circle') {
        return d3.symbolCircle;
    }
    if (legend.shape === 'cross') {
        return d3.symbolCross;
    }
    if (legend.shape === 'diamond') {
        return d3.symbolDiamond;
    }
    if (legend.shape === 'square') {
        return d3.symbolSquare;
    }
    if (legend.shape === 'star') {
        return d3.symbolStar;
    }
    if (legend.shape === 'triangle') {
        return d3.symbolTriangle;
    }
    if (legend.shape === 'wye') {
        return d3.symbolWye;
    }
}

function getLegendColor(legend) {

    return color(legend.label); // use color schemeCategory10
    //return node.fill; // directly assign fill color
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
    textElements.attr('fill', 'black');
    linkElements.attr('stroke', 'rgba(50, 50, 50, 0.2)');
}

// define container
//var width = window.innerWidth, height = window.innerHeight/2;
var margin = {top: 30, right: 10, bottom: 30, left: 10}
var width = parseInt(d3.select('#visualization').style('width')), height = window.innerHeight;
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
//TODO: assign charge for a group nodes
    .force('charge', d3.forceManyBody().strength(-10))
    // draw them around the centre of the space
    .force('center', d3.forceCenter(width / 2, height / 2))
    // pull nodes together based on the links between them
    .force('link', d3.forceLink().id(link => link.id).strength(link => link.strength))
    // add some collision detection so they don't overlap
    .force("collide", d3.forceCollide().radius(30))
    .force('x', d3.forceX(width / 2).strength(0.01))
    .force('y', d3.forceY(height / 2).strength(0.01));

var color = d3.scaleOrdinal(d3.schemeCategory10);
var shape = d3.scaleOrdinal(d3.symbols);

// define nodes, texts, links and drag&drop
var nodeElements = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('.path')
    .data(nodes)
    .enter().append('path')
    // three different methods to change shapes
    //.attr("d", d3.symbol().type(d3.symbolCross))
    //.attr("d", d3.symbol().type( function(d) { return shape(d.type);} ))
    .attr('d', d3.symbol()
        .type(getNodeType)
        .size(getNodeSize))
    .attr("fill", getNodeColor)
    // mouse event
    .on('click', selectNode)
    .on('mouseover', selectNode)
    .on('mouseout', mouseOut)
    .call(d3.drag()
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
        }));
var textElements = svg.append('g')
    .attr('class', 'texts')
    .selectAll('text')
    .data(nodes)
    .enter().append('text')
    .attr('text-anchor', 'middle')
    .text(node => node.label)
    .attr('font-size', 15)
    //.attr('dx', 15)
    .attr('dy', -4);
var linkElements = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('stroke-width', 1)
    .attr('stroke', 'rgba(50, 50, 50, 0.2)');

var legend = svg.append('g')
    .attr('transform', 'translate(20,20)')
    .selectAll('legend')
    .data(legends)
    .enter().append('g')
    .attr('class', 'legend')
    .attr('transform', function (d, i) {
        return 'translate(0,' + i * 20 + ')';
    });
legend.append('path')
    .attr('d', d3.symbol()
        .type(getLegendType)
        .size(100))
    .attr('fill', getLegendColor);

legend.append("text")
    .attr("x", 18)
    .attr("y", -3)
    .attr("dy", ".35em")
    .style("text-anchor", "begin")
    .text(function (d) {
        return d.label;
    });

// setup
simulation.nodes(nodes).on('tick', () => {
    nodeElements.attr('transform', function (d) {
        return 'translate(' + d.x + ',' + d.y + ')';
    });
    //   .attr('cx', node => node.x)
    // .attr('cy', node => node.y);
    textElements
        .attr('x', node => node.x)
        .attr('y', node => node.y);
    linkElements
        .attr('x1', link => link.source.x)
        .attr('y1', link => link.source.y)
        .attr('x2', link => link.target.x)
        .attr('y2', link => link.target.y);
});
simulation.force('link').links(links);