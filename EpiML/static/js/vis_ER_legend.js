var legend_margin = {top: 30, right: 10, bottom: 30, left: 10};
var legend_width = parseInt(d3.select('#visualization').style('width')), legend_height = '30px';
var ER_legendDiv = d3.select('#ER_legendDiv').selectAll('.er_legend');

//	d3.v4 color scales. use definition in vis_ER.js
//var ER_color = d3.scaleOrdinal(d3.schemeCategory10);
//var shape = d3.scaleOrdinal(d3.symbols);

/*
var ER_legends = legend_svg.append('g').attr('class', 'er_legends').attr('transform', 'translate(20,20)')
    .selectAll('legend');
*/

//	data read and store
d3.json(legends_json, function (err, g) {
    if (err) throw err;

    // for legend
    ER_legends = ER_legendDiv.data(g.legends)
        .enter().append('div')
        .attr('class', 'er_legend')
        .classed('col-sm-4', true)
        .append('label');

    // add checkbox
    ER_legends.append('input')
        .attr('type', 'checkbox')
        .attr('class', 'filter-ckb')
        .attr('value', function (l) {
            return l.label;
        })
        .property('checked', true);

    // add shape
    ER_legendsSvg = ER_legends.append('svg')
        .attr('width', '150px')
        .attr('height', '13px')
        .append('g')
        .attr('class', 'legend')
        .attr('transform', function (d, i) {
            return 'translate(12,8)';
        });


    ER_legendsSvg.append('path')
        .attr('d', d3.symbol()
            .type(getLegendType)
            .size(100))
        .attr('fill', getLegendColor);
    // add label
    ER_legendsSvg.append("text")
        .attr("x", 10)
        .attr("y", -2)
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