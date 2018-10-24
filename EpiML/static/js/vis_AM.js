var am_margin = {top: 80, right: 0, bottom: 10, left: 80},
    am_width = parseInt(d3.select('#vis_am').style('width')),
    am_height = am_width,
    am_legend_width = 80,
    am_gap = 10;

var x = d3.scaleBand().range([0, am_width]),
    //z = d3.scaleLinear().domain([-1, 1]).clamp(true),
    z = d3.scaleLinear().range([0.1, 0.9]),
    c = d3.scaleSequential(d3.interpolateBlues);
//c = d3.scaleOrdinal(d3.schemeCategory10).domain(d3.range(1));

var am_svg = d3.select("#adjacency_matrix")
    .attr("width", am_width + am_margin.left + am_margin.right + am_legend_width + am_gap)
    .attr("height", am_height + am_margin.top + am_margin.bottom)
    .style("margin-left", -am_margin.left + "px")
    .append("g")
    .attr("transform", "translate(" + am_margin.left + "," + am_margin.top + ")");

var am_nodes;

d3.json(am_graph_json, function (am_graph) {
    var am_matrix = [];
    am_nodes = am_graph.nodes;
    n = am_nodes.length;

    // Compute index per node.
    am_nodes.forEach(function (node, i) {
        node.index = i;
        node.count = 0;
        am_matrix[i] = d3.range(n).map(function (j) {
            return {x: j, y: i, z: 0};
        });
    });

    // Convert links to matrix; count character occurrences.
    am_graph.links.forEach(function (link) {
        am_matrix[link.source][link.target].z += link.coff;
        am_matrix[link.target][link.source].z += link.coff;
        //am_matrix[link.source][link.source].z = link.coff;
        //am_matrix[link.target][link.target].z = link.coff;

        // count number of association
        am_nodes[link.source].count += Math.ceil(Math.abs(link.coff));
        am_nodes[link.target].count += Math.ceil(Math.abs(link.coff));
    });

    // Precompute the orders.
    var orders = {
        name: d3.range(n).sort(function (a, b) {
            return d3.ascending(am_nodes[a].name, am_nodes[b].name);
        }),
        count: d3.range(n).sort(function (a, b) {
            return am_nodes[b].count - am_nodes[a].count;
        }),
        rank: d3.range(n).sort(function (a, b) {
            return am_nodes[a].rank - am_nodes[b].rank;
        })
    };

    // The default sort order.
    x.domain(orders.name);

    max_abs = d3.max(am_graph.links, function (d) {
        return Math.abs(d.coff);
    });

    z.domain([-max_abs, max_abs]).clamp(true);

    am_svg.append("rect")
        .attr("class", "background")
        .attr("width", am_width)
        .attr("height", am_height);

    var row = am_svg.selectAll(".am_row")
        .data(am_matrix)
        .enter().append("g")
        .attr("class", "am_row")
        .attr("transform", function (d, i) {
            return "translate(0," + x(i) + ")";
        })
        .each(row);

    row.append("line")
        .attr("x2", am_width);

    row.append("text")
        .attr('class', 'am_text')
        .attr("x", -6)
        .attr("y", x.bandwidth() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "end")
        .text(function (d, i) {
            return am_nodes[i].name;
        });

    var column = am_svg.selectAll(".am_column")
        .data(am_matrix)
        .enter().append("g")
        .attr("class", "am_column")
        .attr("transform", function (d, i) {
            return "translate(" + x(i) + ")rotate(-90)";
        });

    column.append("line")
        .attr("x1", -am_width);

    column.append("text")
        .attr('class', 'am_text')
        .attr("x", 6)
        .attr("y", x.bandwidth() / 2)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d, i) {
            return am_nodes[i].name;
        });

    //add a legend for the color values
    var am_legend = am_svg.selectAll('.am_legend')
        .data(z.ticks(20).reverse())
        .enter().append('g')
        .attr('class', '.am_legend')
        .attr('transform', function (d, i) {
            return "translate(" + (am_width + am_gap) + "," + (i * am_width / z.ticks(20).length) + ")";
        });
    am_legend.append('rect')
        .attr('width', 20)
        .attr('height', am_width / z.ticks(20).length)
        .style('fill', function (d) {
            return c(z(d))
        });

    am_legend.append('text')
        .attr('x', 26)
        .attr('y', 10)
        .attr('dy', '.35em')
        .text(String);

    var am_tooltip = d3.select('body')
        .append('div')
        .attr('class', 'am_tooltip')
        .style('opacity', 0);

    function row(row) {
        var cell = d3.select(this).selectAll(".am_cell")
            .data(row.filter(function (d) {
                return d.z;
            }))
            .enter().append("rect")
            .attr("class", "am_cell")
            .attr("x", function (d) {
                return x(d.x);
            })
            .attr("width", x.bandwidth())
            .attr("height", x.bandwidth())
            //.style("fill-opacity", function (d) {
            //   return z(d.z);
            //})
            .style("fill", function (d) {
                //return am_nodes[d.x].group === am_nodes[d.y].group ? c(am_nodes[d.x].group) : null;
                return c(z(d.z));
            })
            .on("mouseover", am_mouseovered)
            //.on("click", am_clicked)
            .on("mouseout", am_mouseouted);
    }

    function am_mouseovered(p) {
        d3.selectAll(".am_row text").classed("active", function (d, i) {
            return i === p.y;
        });
        d3.selectAll(".am_row line").classed("active", function (d, i) {
            return i === p.y;
        });

        d3.selectAll(".am_column text").classed("active", function (d, i) {
            return i === p.x;
        });
        d3.selectAll(".am_column line").classed("active", function (d, i) {
            return i === p.x;
        });

        am_tooltip.transition()
            .duration(300)
            .style("opacity", .9);
        am_tooltip
            .html("Value: " + p.z)
            .style("left", (d3.event.pageX) + "px")
            .style("top", (d3.event.pageY + 10) + "px");
    }

    function am_clicked(p) {
        am_tooltip.transition()
            .duration(300)
            .style("opacity", .9);
        am_tooltip
            .html("Value: " + p.z)
            .style("left", (d3.event.pageX) + "px")
            .style("top", (d3.event.pageY + 10) + "px");
    }

    function am_mouseouted() {
        d3.selectAll("text").classed("active", false);
        d3.selectAll("line").classed("active", false);

        am_tooltip.transition()
            .duration(100)
            .style("opacity", 0)
            .style("left", (am_width + 10) + "px")
            .style("top", (am_height + 10) + "px");
    }

    d3.select("#order").on("change", function () {
        order(this.value);
    });

    function order(value) {
        x.domain(orders[value]);

        var t = am_svg.transition().duration(2500);

        t.selectAll(".am_row")
            .delay(function (d, i) {
                return x(i) * 4;
            })
            .attr("transform", function (d, i) {
                return "translate(0," + x(i) + ")";
            })
            .selectAll(".am_cell")
            .delay(function (d) {
                return x(d.x) * 4;
            })
            .attr("x", function (d) {
                return x(d.x);
            });

        t.selectAll(".am_column")
            .delay(function (d, i) {
                return x(i) * 4;
            })
            .attr("transform", function (d, i) {
                return "translate(" + x(i) + ")rotate(-90)";
            });
    }
});

// Set-up the export button for circle_network
d3.select('#am_saveAsPNG').on('click', function () {
    saveSvgAsPng(document.getElementById("adjacency_matrix"), "adjacency_matrix.png", {scale: 4});
});

d3.select("#am_saveAsSVG")
    .on("click", function () {
        try {
            var isFileSaverSupported = !!new Blob();
        } catch (e) {
            alert("blob not supported");
        }

        var html = d3.select("#adjacency_matrix")
            .attr("title", "saveAsSVG")
            .attr("version", 1.1)
            .attr("xmlns", "http://www.w3.org/2000/cn_svg")
            .node().parentNode.innerHTML;

        var blob = new Blob([html], {type: "image/cn_svg+xml"});
        saveAs(blob, "adjacency_matrix.svg");
    });