var legend_margin = {top: 30, right: 10, bottom: 30, left: 10};
var legend_width = parseInt(d3.select('#visualization').style('width')), legend_height = '30px';
var legend_svg = d3.select('#ER_legend')
    .attr('width', legend_width - legend_margin.left - legend_margin.right)
    .attr('height', legend_height);

//	d3.v4 color scales. use definition in vis_ER.js
//var ER_color = d3.scaleOrdinal(d3.schemeCategory10);
//var shape = d3.scaleOrdinal(d3.symbols);

var ER_legends = legend_svg.append('g').attr('class', 'er_legends').attr('transform', 'translate(20,20)')
    .selectAll('legend');

//	data read and store
d3.json(legends_json, function (err, g) {
    if (err) throw err;

    // for legend
    ER_legends = ER_legends.data(g.legends)
        .enter().append('g')
        .attr('class', 'legend')
        .attr('transform', function (d, i) {
            return 'translate(' + i * 150 + ',0)';
        });
    ER_legends.append('path')
        .attr('d', d3.symbol()
            .type(getLegendType)
            .size(100))
        .attr('fill', getLegendColor);
    ER_legends.append("text")
        .attr("x", 18)
        .attr("y", -3)
        .attr("dy", ".35em")
        .style("text-anchor", "begin")
        .text(function (d) {
            return d.label;
        });

});

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

    return ER_color(legend.label); // use color schemeCategory10
    //return node.fill; // directly assign fill color
}