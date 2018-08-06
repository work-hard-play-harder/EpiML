//	data stores
var FD_graph, FD_store;
var radius = 55;
// define container
//var width = window.innerWidth, height = window.innerHeight/2;
var margin = {top: 30, right: 10, bottom: 30, left: 10};
var width = parseInt(d3.select('#visualization').style('width')), height = window.innerHeight / 1.5;
var svg = d3.select('#FD_diagram')
    .attr('width', width - margin.left - margin.right)
    .attr('height', height)
    // call d3 zoom event, must append a g tag

    .call(d3.zoom().on("zoom", function () {
        svg.attr("transform", d3.event.transform)
    }))
    .append('g');

//	d3.v4 color scales
var color = d3.scaleOrdinal(d3.schemeCategory10);
var shape = d3.scaleOrdinal(d3.symbols);

var FD_nodes = svg.append('g').attr('class', 'nodes').selectAll('.path'),
    FD_links = svg.append('g').attr('class', 'links').selectAll('line');

// define simulator
var simulation = d3.forceSimulation()
// push nodes apart to space them out
//TODO: assign charge for a group nodes
    .force('charge', d3.forceManyBody().strength(-5))
    // .force('charge', d3.forceManyBody())
    // draw them around the centre of the space
    .force('center', d3.forceCenter(width / 2, height / 2))
    // pull nodes together based on the links between them
    .force('link', d3.forceLink().id(link => link.id).strength(link => link.strength))
    //    .force('link', d3.forceLink().id(link => link.id).distance(20))
    // add some collision detection so they don't overlap
    .force("collide", d3.forceCollide().radius(20));
//.force('x', d3.forceX(width / 2).strength(0.01))
//.force('y', d3.forceY(height / 2).strength(0.01));

//	filtered types
var typeFilterList = [];
//	filter button event handlers
$('input.filter-ckb').click(function () {
    typeFilterList = [];
    $('input.filter-ckb').each(function () {
        typeFilterList.push($(this).val());
    });
    $('input.filter-ckb:checked').each(function () {
        typeFilterList.splice(typeFilterList.indexOf($(this).val()), 1);
    });

    filter();
    update();
});

//	data read and store
d3.json(json_file, function (err, g) {
    if (err) throw err;

    var nodeByID = {};
    g.nodes.forEach(function (n) {
        nodeByID[n.id] = n;
    });

    g.links.forEach(function (l) {
        l.sourceGroup = nodeByID[l.source].group.toString();
        l.targetGroup = nodeByID[l.target].group.toString();
    });

    FD_graph = g;
    FD_store = $.extend(true, {}, g);

    update();
});

function update() {
    //UPDATE
    FD_nodes = FD_nodes.data(FD_graph.nodes, function (d) {
        return d.id;
    });
    //EXIT
    FD_nodes.exit().remove();
    //ENTER
    var new_FD_nodes = FD_nodes.enter().append('g');
    new_FD_nodes.append('path')
    // three different methods to change shapes
    //.attr("d", d3.symbol().type(d3.symbolCross))
    //.attr("d", d3.symbol().type( function(d) { return shape(d.type);} ))
        .attr('d', d3.symbol()
            .type(getNodeType)
            .size(getNodeSize))
        .attr("fill", getNodeColor)
        // mouse event
        //.on('click', mouseClickNodeTooltip)
        //.on('mouseover', nodeHighLight)
        .on('mouseover.tooltip', mouseOverNodeTooltip)
        .on('mouseout', mouseOut)
        //.on("mouseout.tooltip",mouseOutNodeTooltip)
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
    //label
    new_FD_nodes.append('text')
        .attr('text-anchor', 'middle')
        .text(node => node.label)
        .attr('font-size', 8)
        //.attr('dx', 15)
        .attr('dy', -4);

    //ENTER + UPDATE
    FD_nodes = FD_nodes.merge(new_FD_nodes);
    /*
        //UPDATE
        FD_nodeText = FD_nodeText.data(FD_graph.nodes, function (d) {
            return d.id;
        });
        //EXIT
        FD_nodeText.exit().remove();
        //ENTER
        var new_FD_nodeText = FD_nodeText.append('text')
            .attr('text-anchor', 'middle')
            .text(node => node.label)
            .attr('font-size', 8)
            //.attr('dx', 15)
            .attr('dy', -4);
        //ENTER + UPDATE
        new_FD_nodeText = FD_nodeText.merge(new_FD_nodeText);
    */
    //UPDATE
    FD_links = FD_links.data(FD_graph.links, function (d) {
        return d.id;
    });
    //EXIT
    FD_links.exit().remove();
    //ENTER
    var new_FD_links = FD_links.enter().append('line')
        .attr('class', 'link')
        .attr('stroke-width', 1)
        .attr('stroke', 'rgba(50, 50, 50, 0.2)');

    new_FD_links.append('title')
        .text(function (d) {
            return 'source: ' + d.source + '\n' + 'target: ' + d.target;
        });
    //ENTER + UPDATE
    FD_links = FD_links.merge(new_FD_links);

    //update simulation nodes, links, and alpha
    simulation.nodes(FD_graph.nodes)
        .on('tick', ticked);
    simulation.force('link')
        .links(FD_graph.links);
    simulation.alpha(1).alphaTarget(0).restart();
}

//	tick event handler with bounded box
function ticked() {
    FD_nodes
        .attr('transform', function (d) {
            return 'translate(' + d.x + ',' + d.y + ')';
        });
    // bounding nodes in a box
    //.attr("cx", function (d) {            return d.x = Math.max(radius, Math.min(width - radius, d.x));        })
    //.attr("cy", function (d) {            return d.y = Math.max(radius, Math.min(height - radius, d.y));        });

    FD_links
        .attr('x1', link => link.source.x)
        .attr('y1', link => link.source.y)
        .attr('x2', link => link.target.x)
        .attr('y2', link => link.target.y);
}

//	filter function
function filter() {
    //	add and remove nodes from data based on type filters
    FD_store.nodes.forEach(function (n) {
        if (!typeFilterList.includes(n.group) && n.filtered) {
            n.filtered = false;
            FD_graph.nodes.push($.extend(true, {}, n));
        } else if (typeFilterList.includes(n.group) && !n.filtered) {
            n.filtered = true;
            FD_graph.nodes.forEach(function (d, i) {
                if (n.id === d.id) {
                    FD_graph.nodes.splice(i, 1);
                }
            });
        }
    });

    //	add and remove links from data based on availability of nodes
    FD_store.links.forEach(function (l) {
        if (!(typeFilterList.includes(l.sourceGroup) || typeFilterList.includes(l.targetGroup)) && l.filtered) {
            l.filtered = false;
            FD_graph.links.push($.extend(true, {}, l));
        } else if ((typeFilterList.includes(l.sourceGroup) || typeFilterList.includes(l.targetGroup)) && !l.filtered) {
            l.filtered = true;
            FD_graph.links.forEach(function (d, i) {
                if (l.id === d.id) {
                    FD_graph.links.splice(i, 1);
                }
            });
        }
    });
}

/*
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
*/
var tooltip = d3.select('body')
    .append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);


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

    return isNeighborLink(node, link) ? 'black' : 'rgba(50, 50, 50, 0.2)'
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
    return FD_links.reduce((neighbors, link) => {
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

function nodeHighLight(selectedNode) {
    var neighbors = getNeighbors(selectedNode);
    FD_nodes.attr('fill', node => getNodeColor(node, neighbors));
    FD_nodeText.attr('fill', node => getTextColor(node, neighbors));
    FD_links.attr('stroke', link => getLinkColor(selectedNode, link));
}

function mouseOverNodeTooltip(node) {
    tooltip.transition()
        .duration(300)
        .style("opacity", .9);
    if (node.level === 1) {
        tooltip
            .html("Name: " + node.id + "<br/>" +
                "Group: " + node.group + "<br/>" +
                "<a href=" + node.url + " target='_blank'>miRBase</a>")
            .style("left", (d3.event.pageX) + "px")
            .style("top", (d3.event.pageY + 10) + "px");
    } else if (node.level === 2) {
        tooltip
            .html("Name: " + node.id + "<br/>" +
                "Group: " + node.group + "<br/>" +
                "<a href=" + node.url + " target='_blank'>miR2Disease</a>")
            .style("left", (d3.event.pageX) + "px")
            .style("top", (d3.event.pageY + 10) + "px");
    }

}

function mouseOut() {
    FD_nodes.attr('fill', node => getNodeColor(node));
    //FD_nodeText.attr('fill', 'black');
    FD_links.attr('stroke', 'rgba(50, 50, 50, 0.2)');
}

function mouseOutNodeTooltip() {
    tooltip.transition()
        .duration(100)
        .style("opacity", 0);
}

function mouseClickNodeTooltip(node) {

}

function mouseOverLinkTooltip(link) {
    tooltip.transition()
        .duration(300)
        .style("opacity", .9);
    tooltip
        .html("Source: " + link.source + "<br/>" +
            "Target: " + link.target + "<br/>" +
            "Ref.:" + "reference" + "<br/>" +
            "<a href='http://www.google.com' target='_blank'>URL FOR TEST</a>")
        .style("left", (d3.event.pageX) + "px")
        .style("top", (d3.event.pageY + 10) + "px");
}

function linkHighLight(link) {
    FD_links.attr('stroke', link => getLinkColor(link.source, link));
    FD_links.attr('stroke', link => getLinkColor(link.target, link));
}

// hide tool tip
d3.select('#FD_diagram').on('click', function () {
    tooltip.transition()
        .duration(100)
        .style("opacity", 0);
});