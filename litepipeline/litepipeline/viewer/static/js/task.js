function taskInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var task_info = {};

    getTaskList();
    $btn_refresh.bind('click', getTaskList);

    function getTaskList(task_id) {
        $.ajax({
            dataType: "json",
            url: "http://" + manager_host + "/task/list",
            success: function(data) {
                $table_header_tr.empty();
                $table_body.empty();
                $table_header_tr.append(getHeaderTR('num', 'num', '#'));
                $table_header_tr.append(getHeaderTR('task_id', 'task id', 'task id'));
                $table_header_tr.append(getHeaderTR('task_name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('application_id', 'application id', 'application id'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('start_at', 'start at', 'start at'));
                $table_header_tr.append(getHeaderTR('end_at', 'end at', 'end at'));
                $table_header_tr.append(getHeaderTR('stage', 'stage', 'stage'));
                $table_header_tr.append(getHeaderTR('status', 'status', 'status'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "task_id",
                    "task_name",
                    "application_id",
                    "create_at",
                    "start_at",
                    "end_at",
                    "stage",
                    "status",
                    "operation"
                ];
                task_info = {};
                data.tasks.forEach(function (value, index, arrays) {
                    task_info[value["task_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + (index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();">detail</button></div></div></td>';
                        } else if (col == 'task_id' || col == 'application_id') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                        } else {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + value[col] + '</div></div></td>';
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
                $(".btn-detail").bind('click', showTaskDetail);

                if (task_id) {
                    var info = {};
                    if (task_info[task_id]) {
                        info = task_info[task_id];
                    }
                    document.getElementById("task_info_json").textContent = JSON.stringify(info, undefined, 4);
                }
            }
        });
    }

    function getHeaderTR(id, title, value) {
        return '<th id="' + id + '" title="' + title + '"><div class="outer"><div class="inner">&nbsp;' + value + '</div></div></th>';
    }

    function refreshTaskInfo(event) {
        var task_id = event.data.task_id;
        getTaskInfo(task_id);
    }

    function showTaskDetail() {
        var task_id = $(this).attr("id");
        document.getElementById("task_info_json").textContent = JSON.stringify(task_info[task_id], undefined, 4);
        $('#task_info_refresh').bind('click', {"task_id": task_id}, refreshTaskInfo);
        $('#task_info_modal').modal('show');
    }

    function addColumnsCSS(keys) {
        var percent = 100.00;
        if (is_in('num', keys)) {
            $('th#num').css("width", "5%");
            $('td#num').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('task_name', keys)) {
            $('th#task_name').css("width", "10%");
            $('td#task_name').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('create_at', keys)) {
            $('th#create_at').css("width", "10%");
            $('td#create_at').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('start_at', keys)) {
            $('th#start_at').css("width", "10%");
            $('td#start_at').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('end_at', keys)) {
            $('th#end_at').css("width", "10%");
            $('td#end_at').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('application_id', keys)) {
            $('th#application_id').css("width", "10%");
            $('td#application_id').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('stage', keys)) {
            $('th#stage').css("width", "5%");
            $('td#stage').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('status', keys)) {
            $('th#status').css("width", "5%");
            $('td#status').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('operation', keys)) {
            $('th#operation').css("width", "8%");
            $('td#operation').css("width", "8%");
            percent -= 8.0;
        }
        if (is_in('task_id', keys)) {
            var width = percent;
            $('th#task_id').css("width", width + "%");
            $('td#task_id').css("width", width + "%");
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