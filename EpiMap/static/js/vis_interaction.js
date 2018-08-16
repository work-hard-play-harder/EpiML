function rowToNetLink(row) {
    cn_nodes
        .each(function (n) {
            n.target = n.source = false;
        });

    cn_links
        .classed("cn_link--target", function (l) {

            if (l.target.data.key === row.data()[2]) return l.source.source = true;
        })
        .classed("cn_link--source", function (l) {
            if (l.source.data.key === row.data()[1]) return l.target.target = true;
        })
        .filter(function (l) {
            return l.target.data.key === row.data()[2] || l.source.data.key === row.data()[1];
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

function rowToMatCell(row) {
    console.log(row.data())
    am_nodes.classed('am_')

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