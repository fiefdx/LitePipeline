function taskInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_task_create = $('#btn_task_create');
    var $btn_task_delete = $('#btn_task_delete');
    var $btn_task_rerun = $('#btn_task_rerun');
    var $btn_task_recover = $('#btn_task_recover');
    var $btn_task_stop = $('#btn_task_stop');
    var $btn_task_download = $('#btn_task_download');
    var task_info = {};
    var current_task_id = "";
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;
    var host = window.location.host;

    getTaskList();
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $("#task_create_modal").on("hidden.bs.modal", resetModal);
    $btn_task_create.bind('click', createTask);
    $btn_task_delete.bind('click', deleteTask);
    $btn_task_rerun.bind('click', rerunTask);
    $btn_task_recover.bind('click', recoverTask);
    $btn_task_stop.bind('click', stopTask);
    $btn_task_download.bind('click', downloadTask);

    function showCreate() {
        $('#task_create_modal').modal('show');
    }

    async function createTask() {
        var data = {};
        data.app_id = $('input#app_id').val();
        data.task_name = $('input#task_name').val();
        var input_data = $('textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#task_create_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/task/create",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getTaskList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getTaskList(task_id) {
        var url = "http://" + manager_host + "/task/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
        if (filter_type) {
            url += "&" + filter_type + "=" + filter_value;
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
                $table_header_tr.append(getHeaderTR('task_id', 'task id', 'task id'));
                $table_header_tr.append(getHeaderTR('task_name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('application_id', 'application id', 'application id'));
                $table_header_tr.append(getHeaderTR('work_id', 'work id', 'work id'));
                $table_header_tr.append(getHeaderTR('service_id', 'service id', 'service id'));
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
                    "work_id",
                    "service_id",
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
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-rerun" onclick="this.blur();"><span class="oi oi-play-circle" title="rerun" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-recover" onclick="this.blur();"><span class="oi oi-circle-check" title="recover" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-stop" onclick="this.blur();"><span class="oi oi-media-stop" title="stop" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-download" onclick="this.blur();"><span class="oi oi-arrow-circle-bottom" title="download" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["task_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'task_id' || col == 'application_id' || col == 'work_id' || col == 'service_id') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                        } else if (col == 'task_name') {
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
                $(".btn-rerun").bind('click', showTaskRerun);
                $(".btn-recover").bind('click', showTaskRecover);
                $(".btn-stop").bind('click', showTaskStop);
                $(".btn-download").bind('click', showTaskDownload);
                $(".btn-delete").bind('click', showTaskDelete);
                $(".btn-detail").bind('click', openTaskInfoPage);

                if (task_id) {
                    var info = {};
                    if (task_info[task_id]) {
                        info = task_info[task_id];
                    }
                    document.getElementById("task_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#task_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#task_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshTaskInfo(event) {
        $('#task_info_refresh').attr("disabled", "disabled");
        var task_id = event.data.task_id;
        getTaskList(task_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getTaskList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getTaskList();
    }

    function showTaskRerun() {
        current_task_id = $(this).attr("id");
        $('#task_rerun_modal').modal('show');
    }

    async function rerunTask() {
        var data = {"task_id": current_task_id};
        $('#task_rerun_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/task/rerun",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getTaskList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showTaskRecover() {
        current_task_id = $(this).attr("id");
        $('#task_recover_modal').modal('show');
    }

    async function recoverTask() {
        var data = {"task_id": current_task_id};
        $('#task_recover_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/task/recover",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getTaskList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showTaskStop() {
        current_task_id = $(this).attr("id");
        $('#task_stop_modal').modal('show');
    }

    async function stopTask() {
        var data = {"task_id": current_task_id, "signal": Number($('#form_stop select#stop_signal').val())};
        $('#task_stop_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/task/stop",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getTaskList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showTaskDownload() {
        current_task_id = $(this).attr("id");
        $("select#action_name").empty();
        var actions = task_info[current_task_id].result;
        for (var action_name in actions) {
            $("select#action_name").append(
                '<option value="' + action_name + '">' + action_name + '</option>'
            );
        }
        $('#task_download_modal').modal('show');
    }

    async function downloadTask() {
        var name = $("select#action_name").val();
        var data = {"task_id": current_task_id, "name": name, "force": true};
        $('#task_download_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        var pack_error = false;
        var download_ready = false;
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/workspace/pack",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: async function(d) {
                if (d.result == "ok") {
                    download_ready = true;
                } else if (d.result == "OperationRunning") {

                } else {
                    pack_error = true;
                }
                await sleep(500);
                while (!pack_error && !download_ready) {
                    data.force = false;
                    $.ajax({
                        type: "PUT",
                        url: "http://" + manager_host + "/workspace/pack",
                        data: JSON.stringify(data),
                        dataType: "json",
                        contentType: false,
                        processData: false,
                        success: async function(d) {
                            if (d.result == "ok") {
                                download_ready = true;
                            } else if (d.result == "OperationRunning") {

                            } else {
                                pack_error = true;
                            }
                        },
                        error: function() {
                            pack_error = true;
                        }
                    });
                    await sleep(1000);
                }
                try {
                    var url = "http://" + manager_host + "/workspace/download?task_id=" + data.task_id;
                    url += "&name=" + data.name;
                    var win = window.open(url, '_blank');
                    win.focus();
                } catch(err) {
                    showWarningToast("error", "request service failed");
                }
                hideWaitScreen();
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
            }
        });
    }

    function showTaskDelete() {
        current_task_id = $(this).attr("id");
        $('#task_delete_modal').modal('show');
    }

    async function deleteTask() {
        $('#task_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/task/delete?task_id=" + current_task_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getTaskList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function openTaskInfoPage() {
        var task_id = $(this).attr("id");
        var url = "http://" + host + "/task/" + task_id;
        var win = window.open(url, '_blank');
        win.focus();
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getTaskList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getTaskList();
    }

    function nextPage() {
        current_page++;
        getTaskList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("textarea").val("");
        $("#" + e.target.id).find('select#stop_signal').val("-9");
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
        if (is_in('work_id', keys)) {
            $('th#work_id').css("width", "10%");
            $('td#work_id').css("width", "10%");
            percent -= 10.0;
        }
        if (is_in('service_id', keys)) {
            $('th#service_id').css("width", "10%");
            $('td#service_id').css("width", "10%");
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
}