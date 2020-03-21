function scheduleInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var schedule_info = {};

    getScheduleList();
    $btn_refresh.bind('click', getScheduleList);

    function getScheduleList(schedule_id) {
        $.ajax({
            dataType: "json",
            url: "http://" + manager_host + "/schedule/list",
            success: function(data) {
                $table_header_tr.empty();
                $table_body.empty();
                $table_header_tr.append(getHeaderTR('num', 'num', '#'));
                $table_header_tr.append(getHeaderTR('schedule_id', 'schedule id', 'schedule id'));
                $table_header_tr.append(getHeaderTR('schedule_name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('application_id', 'application id', 'application id'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('update_at', 'update at', 'update at'));
                $table_header_tr.append(getHeaderTR('hour', 'hour', 'hour'));
                $table_header_tr.append(getHeaderTR('minute', 'minute', 'minute'));
                $table_header_tr.append(getHeaderTR('day_of_week', 'day of week', 'day of week'));
                $table_header_tr.append(getHeaderTR('day_of_month', 'day of month', 'day of month'));
                $table_header_tr.append(getHeaderTR('enable', 'enable', 'enable'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "schedule_id",
                    "schedule_name",
                    "application_id",
                    "create_at",
                    "update_at",
                    "hour",
                    "minute",
                    "day_of_week",
                    "day_of_month",
                    "enable",
                    "operation"
                ];
                schedule_info = {};
                data.schedules.forEach(function (value, index, arrays) {
                    schedule_info[value["schedule_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + (index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><button id="' + value["schedule_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();">detail</button></div></div></td>';
                        } else if (col == 'schedule_id' || col == 'application_id') {
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
                $(".btn-detail").bind('click', showScheduleDetail);

                if (schedule_id) {
                    var info = {};
                    if (schedule_info[schedule_id]) {
                        info = schedule_info[schedule_id];
                    }
                    document.getElementById("schedule_info_json").textContent = JSON.stringify(info, undefined, 4);
                }
            }
        });
    }

    function getHeaderTR(id, title, value) {
        return '<th id="' + id + '" title="' + title + '"><div class="outer"><div class="inner">&nbsp;' + value + '</div></div></th>';
    }

    function refreshScheduleInfo(event) {
        var schedule_id = event.data.schedule_id;
        getScheduleInfo(schedule_id);
    }

    function showScheduleDetail() {
        var schedule_id = $(this).attr("id");
        document.getElementById("schedule_info_json").textContent = JSON.stringify(schedule_info[schedule_id], undefined, 4);
        $('#schedule_info_refresh').bind('click', {"schedule_id": schedule_id}, refreshScheduleInfo);
        $('#schedule_info_modal').modal('show');
    }

    function addColumnsCSS(keys) {
        var percent = 100.00;
        if (is_in('num', keys)) {
            $('th#num').css("width", "5%");
            $('td#num').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('schedule_name', keys)) {
            $('th#schedule_name').css("width", "10%");
            $('td#schedule_name').css("width", "10%");
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
        if (is_in('application_id', keys)) {
            $('th#application_id').css("width", "10%");
            $('td#application_id').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('operation', keys)) {
            $('th#operation').css("width", "8%");
            $('td#operation').css("width", "8%");
            percent -= 8.0;
        }
        if (is_in('hour', keys)) {
            $('th#hour').css("width", "3%");
            $('td#hour').css("width", "3%");
            percent -= 3.0;
        }
        if (is_in('minute', keys)) {
            $('th#minute').css("width", "3%");
            $('td#minute').css("width", "3%");
            percent -= 3.0;
        }
        if (is_in('day_of_week', keys)) {
            $('th#day_of_week').css("width", "6%");
            $('td#day_of_week').css("width", "6%");
            percent -= 6.0;
        }
        if (is_in('day_of_month', keys)) {
            $('th#day_of_month').css("width", "6%");
            $('td#day_of_month').css("width", "6%");
            percent -= 6.0;
        }
        if (is_in('enable', keys)) {
            $('th#enable').css("width", "3%");
            $('td#enable').css("width", "3%");
            percent -= 3.0;
        }
        if (is_in('schedule_id', keys)) {
            var width = percent;
            $('th#schedule_id').css("width", width + "%");
            $('td#schedule_id').css("width", width + "%");
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