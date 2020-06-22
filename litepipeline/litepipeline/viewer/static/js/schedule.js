function scheduleInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_schedule_create = $('#btn_schedule_create');
    var $btn_schedule_update = $('#btn_schedule_update');
    var $btn_schedule_delete = $('#btn_schedule_delete');
    var schedule_info = {};
    var current_schedule_id = "";
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;

    generateSelectList('day_of_month', dayOfMonthIter());
    generateSelectList('hour', hourIter());
    generateSelectList('minute', minuteIter());
    getScheduleList();
    $("#schedule_create_modal").on("hidden.bs.modal", resetModal);
    $("#schedule_update_modal").on("hidden.bs.modal", resetModal);
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $btn_schedule_create.bind('click', createSchedule);
    $btn_schedule_update.bind('click', updateSchedule);
    $btn_schedule_delete.bind('click', deleteSchedule);

    function showCreate() {
        $('#schedule_create_modal').modal('show');
    }

    async function createSchedule() {
        var data = {};
        data.schedule_name = $('#form_create input#schedule_name').val();
        data.source = $('#form_create select#source').val();
        data.source_id = $('#form_create input#source_id').val();
        data.day_of_month = Number($('#form_create select#day_of_month').val());
        data.day_of_week = Number($('#form_create select#day_of_week').val());
        data.hour = Number($('#form_create select#hour').val());
        data.minute = Number($('#form_create select#minute').val());
        data.enable = $('#form_create input#enable').is(":checked");
        var input_data = $('#form_create textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#schedule_create_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/schedule/create",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getScheduleList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getScheduleList(schedule_id) {
        var url = "http://" + manager_host + "/schedule/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
        if (filter_type) {
            if (filter_type == "app_id" || filter_type == "workflow_id") {
                url += "&source_id=" + filter_value;
            } else {
                url += "&" + filter_type + "=" + filter_value;
            }
        }
        $.ajax({
            dataType: "json",
            url: url,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                $table_header_tr.empty();
                $table_body.empty();
                $table_header_tr.append(getHeaderTR('num', 'num', '#'));
                $table_header_tr.append(getHeaderTR('schedule_id', 'schedule id', 'schedule id'));
                $table_header_tr.append(getHeaderTR('schedule_name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('source', 'source', 'source'));
                $table_header_tr.append(getHeaderTR('source_id', 'source id', 'source id'));
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
                    "source",
                    "source_id",
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
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["schedule_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["schedule_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["schedule_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'schedule_id' || col == 'source_id') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                        } else if (col == 'schedule_name') {
                            tr += '<td id="' + col + '" title="' + value[col] + '"><div class="outer"><div class="inner">&nbsp;' + value[col] + '</div></div></td>';
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
                $(".btn-update").bind('click', showScheduleUpdate);
                $(".btn-delete").bind('click', showScheduleDelete);
                $(".btn-detail").bind('click', showScheduleDetail);

                if (schedule_id) {
                    var info = {};
                    if (schedule_info[schedule_id]) {
                        info = schedule_info[schedule_id];
                    }
                    document.getElementById("schedule_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#schedule_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#schedule_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshScheduleInfo(event) {
        $('#schedule_info_refresh').attr("disabled", "disabled");
        var schedule_id = event.data.schedule_id;
        getScheduleList(schedule_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getScheduleList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getScheduleList();
    }

    function showScheduleUpdate() {
        current_schedule_id = $(this).attr("id");
        var info = schedule_info[current_schedule_id];
        $('#form_update input#schedule_name').val(info.schedule_name);
        $('#form_update select#source').val(info.source);
        $('#form_update input#source_id').val(info.source_id);
        $('#form_update select#day_of_month').val(info.day_of_month);
        $('#form_update select#day_of_week').val(info.day_of_week);
        $('#form_update select#hour').val(info.hour);
        $('#form_update select#minute').val(info.minute);
        $('#form_update input#enable').prop("checked", info.enable);
        $('#form_update textarea#input_data').val(JSON.stringify(info.input_data), undefined, 4);
        $('#schedule_update_modal').modal('show');
    }

    async function updateSchedule() {
        var data = {};
        data.schedule_id = current_schedule_id;
        var schedule_name = $('#form_update input#schedule_name').val();
        if (schedule_name) {
            data.schedule_name = schedule_name;
        }
        data.source = $('#form_update select#source').val();
        var source_id = $('#form_update input#source_id').val();
        if (source_id) {
            data.source_id = source_id;
        }
        data.day_of_month = Number($('#form_update select#day_of_month').val());
        data.day_of_week = Number($('#form_update select#day_of_week').val());
        data.hour = Number($('#form_update select#hour').val());
        data.minute = Number($('#form_update select#minute').val());
        data.enable = $('#form_update input#enable').is(":checked");
        var input_data = $('#form_update textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#schedule_update_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/schedule/update",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getScheduleList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showScheduleDelete() {
        current_schedule_id = $(this).attr("id");
        $('#schedule_delete_modal').modal('show');
    }

    async function deleteSchedule() {
        $('#schedule_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/schedule/delete?schedule_id=" + current_schedule_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getScheduleList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showScheduleDetail() {
        var schedule_id = $(this).attr("id");
        document.getElementById("schedule_info_json").textContent = JSON.stringify(schedule_info[schedule_id], undefined, 4);
        $('#schedule_info_refresh').bind('click', {"schedule_id": schedule_id}, refreshScheduleInfo);
        $('#schedule_info_modal').modal('show');
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getScheduleList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getScheduleList();
    }

    function nextPage() {
        current_page++;
        getScheduleList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("select").val(-1);
        $("#" + e.target.id).find('select#source').val("application");
        $("#" + e.target.id).find("input[type='number']").val("-1");
        $("#" + e.target.id).find("textarea").val("");
        $("#" + e.target.id).find('input#enable').prop("checked", false);
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
        if (is_in('source', keys)) {
            $('th#source').css("width", "5%");
            $('td#source').css("width", "5%");
            percent -= 5.0;
        }
        if (is_in('source_id', keys)) {
            $('th#source_id').css("width", "10%");
            $('td#source_id').css("width", "10%");
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
}