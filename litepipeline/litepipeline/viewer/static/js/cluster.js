function clusterInit (manager_host) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");

    getClusterInfo();
    $btn_refresh.bind('click', getClusterInfo);

    function getClusterInfo() {
        $.ajax({
            dataType: "json",
            url: "http://" + manager_host + "/cluster/info",
            success: function(data) {
                $table_header_tr.empty();
                $table_body.empty();
                $table_header_tr.append('<th id="num">&nbsp;#</th>');
                $table_header_tr.append('<th id="node_id">&nbsp;node id</th>');
                $table_header_tr.append('<th id="http_host">&nbsp;http host</th>');
                $table_header_tr.append('<th id="http_port">&nbsp;http port</th>');
                $table_header_tr.append('<th id="action_slots">&nbsp;action slots</th>');
                $table_header_tr.append('<th id="version">&nbsp;version</th>');
                var columns = [
                    "num",
                    "node_id",
                    "http_host",
                    "http_port",
                    "action_slots",
                    "version"
                ];
                data.info.nodes.forEach(function (value, index, arrays) {
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + (index + 1) + '</div></div></td>';
                        } else {
                            if (value[col]) {
                                tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + value[col] + '</div></div></td>';
                            }
                        }
                    }
                    tr += '</tr>';
                    $table_body.append(tr);
                });
                addColumnsCSS(columns);
            }
        });
    }

    function addColumnsCSS(keys) {
        console.log("css: ", keys, "num" == keys[0]);
        var percent = 100.00;
        if (is_in('num', keys)) {
            $('th#num').css("width", "5%");
            $('td#num').css("width", "5%");
            percent -= 5.0;
            console.log("percent: ", percent);
        }
        if (is_in('http_host', keys)) {
            $('th#http_host').css("width", "10%");
            $('td#http_host').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('http_port', keys)) {
            $('th#http_port').css("width", "5%");
            $('td#http_port').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('action_slots', keys)) {
            $('th#action_slots').css("width", "5%");
            $('td#action_slots').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('version', keys)) {
            $('th#version').css("width", "10%");
            $('td#version').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('node_id', keys)) {
            var width = percent;
            $('th#node_id').css("width", width + "%");
            $('td#node_id').css("width", width + "%");
        }
    }

    function is_in(v, l) {
        for (var i=0; i<l.length; i++) {
            if (v == l[i]) {
                return true;
            }
        }
        return false;
    }

    function hasVerticalScrollBar(el) {
        var result = el.scrollHeight > el.clientHeight;
        return result;
    }

    function getBrowserScrollSize() {
        var css = {
            "border":  "none",
            "height":  "200px",
            "margin":  "0",
            "padding": "0",
            "width":   "200px"
        };

        var inner = $("<div>").css($.extend({}, css));
        var outer = $("<div>").css($.extend({
            "left":       "-1000px",
            "overflow":   "scroll",
            "position":   "absolute",
            "top":        "-1000px"
        }, css)).append(inner).appendTo("body")
        .scrollLeft(1000)
        .scrollTop(1000);

        var scrollSize = {
            "height": (outer.offset().top - inner.offset().top) || 0,
            "width": (outer.offset().left - inner.offset().left) || 0
        };

        outer.remove();
        return scrollSize;
    }
}