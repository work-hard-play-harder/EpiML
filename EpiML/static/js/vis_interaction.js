function rowToNetLink(row) {
    console.log(row.data());
    cn_nodes
        .each(function (n) {
            n.target = n.source = false;
        });

    cn_links
        .classed("cn_click_link--target", function (l) {
            console.log(l.target.data, l.source);
            if (l.target.data.key === row.data()[2]) return l.source.target= true;
        })
        .classed("cn_click_link--source", function (l) {
            if (l.source.data.key === row.data()[1]) return l.target.source  = true;
        })
        .filter(function (l) {
            return l.target.data.key === row.data()[2] || l.source.data.key === row.data()[1];
        })
        .raise();

    cn_nodes
        .classed("cn_click_node--target", function (n) {
            return n.target;
        })
        .classed("cn_click_node--source", function (n) {
            return n.source;
        });
}

function rowToMatCell(row) {
    var sourceIndex, targetIndex;
    am_nodes.forEach(function (n) {
        if (n.name === row.data()[1]) {
            sourceIndex = n.index;
        }
        if (n.name === row.data()[2]) {
            targetIndex = n.index;
        }
    });
    d3.selectAll(".am_row text").classed("click", function (d, i) {
        return i === targetIndex;
    });
    d3.selectAll(".am_row line").classed("click", function (d, i) {
        return i === targetIndex;
    });

    d3.selectAll(".am_column text").classed("click", function (d, i) {
        return i === sourceIndex;
    });
    d3.selectAll(".am_column line").classed("click", function (d, i) {
        return i === sourceIndex;
    });
}

$(document).ready(function () {
    $('#main_effect').DataTable();

    var epis_table = $('#epis_effect').DataTable();

    $('#epis_effect tbody').on('click', 'tr', function () {
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
        }
        else {
            epis_table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }

        rowToNetLink(epis_table.row('.selected'));
        rowToMatCell(epis_table.row('.selected'));
    });
});