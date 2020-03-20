function applicationInit (manager_host) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var application_info = {};

    getAppList();
    $btn_refresh.bind('click', getAppList);

    function getAppList(application_id) {
        $.ajax({
            dataType: "json",
            url: "http://" + manager_host + "/app/list",
            success: function(data) {
                $table_header_tr.empty();
                $table_body.empty();
                $table_header_tr.append('<th id="num">&nbsp;#</th>');
                $table_header_tr.append('<th id="application_id">&nbsp;application id</th>');
                $table_header_tr.append('<th id="name">&nbsp;name</th>');
                $table_header_tr.append('<th id="sha1">&nbsp;sha1</th>');
                $table_header_tr.append('<th id="create_at">&nbsp;create at</th>');
                $table_header_tr.append('<th id="update_at">&nbsp;update at</th>');
                $table_header_tr.append('<th id="operation">&nbsp;operation</th>');
                var columns = [
                    "num",
                    "application_id",
                    "name",
                    "sha1",
                    "create_at",
                    "update_at",
                    "operation"
                ];
                application_info = {};
                data.apps.forEach(function (value, index, arrays) {
                    application_info[value["application_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + (index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();">detail</button></div></div></td>';
                        } else if (col == 'application_id' || col == 'sha1') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                        } else {
                            if (value[col]) {
                                tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + value[col] + '</div></div></td>';
                            }
                        }
                    }
                    tr += '</tr>';
                    $table_body.append(tr);
                });

                var tbody = document.getElementById("table_body");
                if (hasVerticalScrollBar(tbody)) {
                    $table_header.css({"margin-right": scrollBarSize.width});
                }
                else {
                    $table_header.css({"margin-right": 0});
                }
                
                addColumnsCSS(columns);
                $(".btn-detail").bind('click', showAppDetail);

                if (application_id) {
                    var info = {};
                    if (application_info[application_id]) {
                        info = application_info[application_id];
                    }
                    document.getElementById("app_info_json").textContent = JSON.stringify(info, undefined, 4);
                }
            }
        });
    }

    function refreshAppInfo(event) {
        var application_id = event.data.application_id;
        getAppInfo(application_id);
    }

    function showAppDetail() {
        var application_id = $(this).attr("id");
        document.getElementById("app_info_json").textContent = JSON.stringify(application_info[application_id], undefined, 4);
        $('#app_info_refresh').bind('click', {"application_id": application_id}, refreshAppInfo);
        $('#app_info_modal').modal('show');
    }

    function addColumnsCSS(keys) {
        var percent = 100.00;
        if (is_in('num', keys)) {
            $('th#num').css("width", "5%");
            $('td#num').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('name', keys)) {
            $('th#name').css("width", "10%");
            $('td#name').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('create_at', keys)) {
            $('th#create_at').css("width", "10%");
            $('td#create_at').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('update_at', keys)) {
            $('th#update_at').css("width", "10%");
            $('td#update_at').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('sha1', keys)) {
            $('th#sha1').css("width", "10%");
            $('td#sha1').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('operation', keys)) {
            $('th#operation').css("width", "8%");
            $('td#operation').css("width", "8%");
            percent -= 8.0;
        }
        if (is_in('application_id', keys)) {
            var width = percent;
            $('th#application_id').css("width", width + "%");
            $('td#application_id').css("width", width + "%");
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