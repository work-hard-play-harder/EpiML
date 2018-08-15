var diameter = parseInt(d3.select('#HEB_canvas').style('width')),
    radius = diameter / 2,
    innerRadius = radius - 150;

var cluster = d3.cluster()
    .size([360, innerRadius]);

var line = d3.radialLine()
    .curve(d3.curveBundle.beta(0.3))
    .radius(function (d) {
        return d.y;
    })
    .angle(function (d) {
        return d.x / 180 * Math.PI;
    });
//TODO: add css in to js for generating good SVG file.
var svg = d3.select("#HEB_diagram")
    .attr("width", diameter)
    .attr("height", diameter)
    .append("g")
    .attr("transform", "translate(" + radius + "," + radius + ")");

var root = packageHierarchy(miRNA_HEB_json)
    .sum(function (d) {
        return d.size;
    });
cluster(root);

var HEB_link = svg.append("g").selectAll(".HEB_link")
    .data(packageImports(root.leaves()))
    .enter().append("path")
    .each(function (d) {
        d.source = d[0], d.target = d[d.length - 1];
    })
    .attr("class", "HEB_link")
    .attr("d", line);

var HEB_node = svg.append("g").selectAll(".HEB_node")
    .data(root.leaves())
    .enter().append("text")
    .attr("class", "HEB_node")
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
    HEB_node
        .each(function (n) {
            n.target = n.source = false;
        });

    HEB_link
        .classed("HEB_link--target", function (l) {
            if (l.target === d) return l.source.source = true;
        })
        .classed("HEB_link--source", function (l) {
            if (l.source === d) return l.target.target = true;
        })
        .filter(function (l) {
            return l.target === d || l.source === d;
        })
        .raise();

    HEB_node
        .classed("HEB_node--target", function (n) {
            return n.target;
        })
        .classed("HEB_node--source", function (n) {
            return n.source;
        });
}


function mouseouted(d) {
    HEB_link
        .classed("HEB_link--target", false)
        .classed("HEB_link--source", false);

    HEB_node
        .classed("HEB_node--target", false)
        .classed("HEB_node--source", false);
}

function mouseclicked(d) {
    $('#epis_effect').DataTable().search(d.data.key)
        .draw();
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
d3.select('#HEB_diagram').on('dblclick', function () {
    $('#epis_effect').DataTable().search('').draw();
});

// Set-up the export button for HEB_diagram
d3.select('#HEB_saveAsPNG').on('click', function () {
    saveSvgAsPng(document.getElementById("HEB_diagram"), "HEB_diagram.png", {scale: 4});
});

d3.select("#HEB_saveAsSVG")
    .on("click", function () {
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = d3.select("#HEB_diagram")
            .attr("title", "saveAsSVG")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/svg")
            .node().parentNode.innerHTML;

        var blob = new Blob([html], {type: "image/svg+xml"});
        saveAs(blob, "HEB_diagram.svg");
    });