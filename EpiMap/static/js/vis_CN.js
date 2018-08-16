var diameter = parseInt(d3.select('#vis_cn').style('width')),
    radius = diameter / 2,
    innerRadius = radius - 150;

var cluster = d3.cluster()
    .size([360, innerRadius]);

var cn_line = d3.radialLine()
    .curve(d3.curveBundle.beta(0.3))
    .radius(function (d) {
        return d.y;
    })
    .angle(function (d) {
        return d.x / 180 * Math.PI;
    });
//TODO: add css in to js for generating good SVG file.
var cn_svg = d3.select("#circle_network")
    .attr("width", diameter)
    .attr("height", diameter)
    .append("g")
    .attr("transform", "translate(" + radius + "," + radius + ")");

var root = packageHierarchy(cn_graph_json)
    .sum(function (d) {
        return d.size;
    });
cluster(root);

var cn_links = cn_svg.append("g").selectAll(".cn_link")
    .data(packageImports(root.leaves()))
    .enter().append("path")
    .each(function (d) {
        d.source = d[0], d.target = d[d.length - 1];
    })
    .attr("class", "cn_link")
    .attr("d", cn_line);

var cn_nodes = cn_svg.append("g").selectAll(".cn_node")
    .data(root.leaves())
    .enter().append("text")
    .attr("class", "cn_node")
    .attr("dy", "0.31em")
    .attr("transform", function (d) {
        return "rotate(" + (d.x - 90) + ")translate(" + (d.y + 8) + ",0)" + (d.x < 180 ? "" : "rotate(180)");
    })
    .attr("text-anchor", function (d) {
        return d.x < 180 ? "start" : "end";
    })
    .text(function (d) {
        return d.data.key;
    })
    .on("mouseover", mouseovered)
    .on("mouseout", mouseouted)
    .on('click', mouseclicked);

function mouseovered(d) {
    cn_nodes
        .each(function (n) {
            n.target = n.source = false;
        });

    cn_links
        .classed("cn_link--target", function (l) {
            if (l.target === d) return l.source.source = true;
        })
        .classed("cn_link--source", function (l) {
            if (l.source === d) return l.target.target = true;
        })
        .filter(function (l) {
            return l.target === d || l.source === d;
        })
        .raise();

    cn_nodes
        .classed("cn_node--target", function (n) {
            return n.target;
        })
        .classed("cn_node--source", function (n) {
            return n.source;
        });
}

function mouseouted(d) {
    cn_links
        .classed("cn_link--target", false)
        .classed("cn_link--source", false);

    cn_nodes
        .classed("cn_node--target", false)
        .classed("cn_node--source", false);
}

function mouseclicked(d) {
    console.log(d)
    $('#epis_effect').DataTable().search(d.data.key)
        .draw();

    cn_nodes
        .each(function (n) {
            n.target = n.source = false;
        });

    cn_links
        .classed("cn_click_link--target", function (l) {
            if (l.target === d) return l.source.source = true;
        })
        .classed("cn_click_link--source", function (l) {
            if (l.source === d) return l.target.target = true;
        })
        .filter(function (l) {
            return l.target === d || l.source === d;
        })
        .raise();

    cn_nodes
        .classed("cn_click_node--target", function (n) {
            return n.target;
        })
        .classed("cn_click_node--source", function (n) {
            return n.source;
        })
        .classed("cn_click_node", function (n) {
            return n === d;
        });
}

// Lazily construct the package hierarchy from class names.
function packageHierarchy(classes) {
    var map = {};

    function find(name, data) {
        var node = map[name], i;
        if (!node) {
            node = map[name] = data || {name: name, children: []};
            if (name.length) {
                node.parent = find(name.substring(0, i = name.lastIndexOf(".")));
                node.parent.children.push(node);
                node.key = name.substring(i + 1);
            }
        }
        return node;
    }

    classes.forEach(function (d) {
        find(d.name, d);
    });

    return d3.hierarchy(map[""]);
}

// Return a list of effects for the given array of nodes.
function packageImports(nodes) {
    var map = {},
        effects = [];

    // Compute a map from name to node.
    nodes.forEach(function (d) {
        map[d.data.name] = d;
    });

    // For each import, construct a link from the source to target node.
    nodes.forEach(function (d) {
        if (d.data.effects) d.data.effects.forEach(function (i) {
            effects.push(map[d.data.name].path(map[i]));
        });
    });
    return effects;
}

// back to search default
d3.select('#circle_network').on('dblclick', function () {
    $('#epis_effect').DataTable().search('').draw();
});

// Set-up the export button for circle_network
d3.select('#cn_saveAsPNG').on('click', function () {
    saveSvgAsPng(document.getElementById("circle_network"), "circle_network.png", {scale: 4});
});

d3.select("#cn_saveAsSVG")
    .on("click", function () {
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = d3.select("#circle_network")
            .attr("title", "saveAsSVG")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/cn_svg")
            .node().parentNode.innerHTML;

        var blob = new Blob([html], {type: "image/cn_svg+xml"});
        saveAs(blob, "circle_network.svg");
    });