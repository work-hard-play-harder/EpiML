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

// retrieve link by two nodes index
var linkedByID = {};

// define links and nodes
// first defined element is in back layer.
var FD_links = svg.append('g').attr('class', 'FD_links').selectAll('.FD_link'),
    FD_nodes = svg.append('g').attr('class', 'FD_nodes').selectAll('.FD_node'),
    FD_legends = svg.append('g').attr('class', 'FD_legends').attr('transform', 'translate(20,20)')
        .selectAll('legend');
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
d3.json(nodes_links_json, function (err, g) {
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

    FD_graph.links.forEach(d => {
        linkedByID[`${d.source},${d.target}`] = 1;
    });

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
        .attr('class', 'FD_node')
        // three different methods to change shapes
        //.attr("d", d3.symbol().type(d3.symbolCross))
        //.attr("d", d3.symbol().type( function(d) { return shape(d.type);} ))
        .attr('d', d3.symbol().type(getNodeType).size(d => d.size))
        .attr("fill", d => color(d.group))
        // mouse event
        .on('click', mouseClickNodeTooltip)
        .on('mouseover', fade(0.1))
        //.on('mouseover.tooltip', mouseOverNodeTooltip)
        .on('mouseout', fade(1))
        //.on("mouseout.tooltip",mouseOutNodeTooltip)
        .call(d3.drag()
            .on('start', node => {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                node.fx = node.x;
                node.fy = node.y;
            })
            .on('drag', node => {
                node.fx = d3.event.x;
                node.fy = d3.event.y;
            })
            .on('end', node => {
                if (!d3.event.active) simulation.alphaTarget(0);
                node.fx = null;
                node.fy = null;
            }));
    //label
    new_FD_nodes.append('text')
        .attr('class', 'FD_text')
        .attr('text-anchor', 'middle')
        .text(node => node.label)
        .attr('font-size', 8)
        //.attr('dx', 15)
        .attr('dy', -4);
    //ENTER + UPDATE
    FD_nodes = FD_nodes.merge(new_FD_nodes);

    //UPDATE
    FD_links = FD_links.data(FD_graph.links, d => d.id);
    //EXITß
    FD_links.exit().remove();
    //ENTER
    var new_FD_links = FD_links.enter().append('line')
        .attr('class', 'FD_link');
    /*
    new_FD_links.append('title')
        .text(function (d) {
            return 'source: ' + d.source + '\n' + 'target: ' + d.target;
        });
    */
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

var tooltip = d3.select('body')
    .append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);


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


function isConnected(a, b) {
    return linkedByID[`${a.id},${b.id}`] || linkedByID[`${b.id},${a.id}`] || a.id === b.id;
}

function fade(opacity) {
    return d => {
        FD_nodes.style('stroke-opacity', function (o) {
            var thisOpacity = isConnected(d, o) ? 1 : opacity;

            this.setAttribute('fill-opacity', thisOpacity);
            return thisOpacity;
        });

        FD_links.style('stroke-opacity', o => (o.source === d || o.target === d ? 1 : opacity));
    };
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

function mouseOutNodeTooltip() {
    tooltip.transition()
        .duration(100)
        .style("opacity", 0);
}

function mouseClickNodeTooltip(node) {
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
    //alert(d3.select('.tooltip').style("opacity"));
    if (d3.select('.tooltip').style("opacity") == 0.9) {
        tooltip.transition()
            .duration(100)
            .style("opacity", 0);
    }
});


// Set-up the export button for FD_diagram
d3.select('#FD_saveAsPNG').on('click', function () {
    saveSvgAsPng(document.getElementById("FD_diagram"), "FD_diagram.png", {scale: 4});
});
d3.select("#FD_saveAsSVG")
    .on("click", function () {
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = d3.select("#FD_diagram")
            .attr("title", "saveAsSVG")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/svg")
            .node().parentNode.innerHTML;

        var blob = new Blob([html], {type: "image/svg+xml"});
        saveAs(blob, "FD_diagram.svg");
    });