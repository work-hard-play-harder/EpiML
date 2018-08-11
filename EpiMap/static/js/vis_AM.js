var am_margin = {top: 80, right: 0, bottom: 10, left: 80},
    am_width = 700,
    am_height = 700;

var x = d3.scaleBand().range([0, am_width]),
    z = d3.scaleLinear().domain([0, 4]).clamp(true),
    c = d3.scaleOrdinal(d3.schemeCategory10).domain(d3.range(10));

var am_svg = d3.select("#adjacency_matrix")
    .attr("width", am_width + am_margin.left + am_margin.right)
    .attr("height", am_height + am_margin.top + am_margin.bottom)
    .style("margin-left", -am_margin.left + "px")
    .append("g")
    .attr("transform", "translate(" + am_margin.left + "," + am_margin.top + ")");

var am_nodes = [], am_node_ids = [], am_links = [];
d3.json(am_graph_json, function (am_graph) {

    var am_matrix = [];

    //filter epistatic nodes and links
    am_graph.nodes.forEach(function (n) {
        if (n.group === 'Epistatic effect') {
            am_nodes.push($.extend(true, {}, n));
            am_node_ids.push(n.id);
        }
    });
    n = am_nodes.length;

    am_graph.links.forEach(function (l) {
        if (am_node_ids.includes(l.source) && am_node_ids.includes(l.target)) {
            am_links.push($.extend(true, {}, l));
        }
    });

    // Compute index per node.
    am_nodes.forEach(function (node_i, i) {
        //am_node_ids[node_i.id].index = i;
        //am_node_ids[node_i.id].count = 0;
        am_matrix[node_i.id] = {};
        am_nodes.forEach(function (node_j, j) {
            am_matrix[node_i.id][node_j.id] = {x: j, y: i, z: 0};
        });
    });

    console.log(am_matrix);
    // Convert links to matrix; count character occurrences.
    am_links.forEach(function (link) {
        am_matrix[link.source][link.target].z += link.coff;
        am_matrix[link.target][link.source].z += link.coff;
        am_matrix[link.source][link.source].z += link.coff;
        am_matrix[link.target][link.target].z += link.coff;

        //am_node_ids[link.source].count += link.coff;
        //am_node_ids[link.target].count += link.coff;
    });


    // Precompute the orders.
    var orders = {
        name: d3.range(n).sort(function (a, b) {
            return d3.ascending(am_nodes[a].id, am_nodes[b].id);
        })
        /*,
        count: d3.range(n).sort(function (a, b) {
            return nodes[b].count - nodes[a].count;
        }),
        group: d3.range(n).sort(function (a, b) {
            return nodes[b].group - nodes[a].group;
        })
        */
    };

    // The default sort order.
    x.domain(orders.name);

    am_svg.append("rect")
        .attr("class", "background")
        .attr("width", width)
        .attr("height", height);

    var row = am_svg.selectAll(".row")
        .data(am_matrix)
        .enter().append("g")
        .attr("class", "row")
        .attr("transform", function (d, i) {
            return "translate(0," + x(i) + ")";
        })
        .each(row);

    row.append("line")
        .attr("x2", width);

    row.append("text")
        .attr("x", -6)
        .attr("y", x.bandwidth() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function (d, i) {
            return am_nodes[i].id;
        });

    var column = am_svg.selectAll(".column")
        .data(am_matrix)
        .enter().append("g")
        .attr("class", "column")
        .attr("transform", function (d, i) {
            return "translate(" + x(i) + ")rotate(-90)";
        });

    column.append("line")
        .attr("x1", -width);

    column.append("text")
        .attr("x", 6)
        .attr("y", x.bandwidth() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d, i) {
            return am_nodes[i].id;
        });

    function row(row) {
        var cell = d3.select(this).selectAll(".cell")
            .data(row.filter(function (d) {
                return d.z;
            }))
            .enter().append("rect")
            .attr("class", "cell")
            .attr("x", function (d) {
                return x(d.x);
            })
            .attr("width", x.bandwidth())
            .attr("height", x.bandwidth())
            .style("fill-opacity", function (d) {
                return z(d.z);
            })
            .style("fill", function (d) {
                return nodes[d.x].group === nodes[d.y].group ? c(nodes[d.x].group) : null;
            })
            .on("mouseover", mouseover)
            .on("mouseout", mouseout);
    }

    function mouseover(p) {
        d3.selectAll(".row text").classed("active", function (d, i) {
            return i === p.y;
        });
        d3.selectAll(".row line").classed("active", function (d, i) {
            return i === p.y;

        });

        d3.selectAll(".column text").classed("active", function (d, i) {
            return i === p.x;
        });
        d3.selectAll(".column line").classed("active", function (d, i) {
            return i === p.x;
        });
    }

    function mouseout() {
        d3.selectAll("text").classed("active", false);
        d3.selectAll("line").classed("active", false);
    }

    d3.select("#order").on("change", function () {

        order(this.value);
    });

    function order(value) {
        x.domain(orders[value]);

        var t = am_svg.transition().duration(2500);

        t.selectAll(".row")
            .delay(function (d, i) {
                return x(i) * 4;
            })
            .attr("transform", function (d, i) {
                return "translate(0," + x(i) + ")";
            })
            .selectAll(".cell")
            .delay(function (d) {
                return x(d.x) * 4;
            })
            .attr("x", function (d) {
                return x(d.x);
            });

        t.selectAll(".column")
            .delay(function (d, i) {
                return x(i) * 4;
            })
            .attr("transform", function (d, i) {
                return "translate(" + x(i) + ")rotate(-90)";
            });
    }


});