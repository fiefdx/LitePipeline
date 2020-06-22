function workInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_work_create = $('#btn_work_create');
    var $btn_work_delete = $('#btn_work_delete');
    var $btn_work_rerun = $('#btn_work_rerun');
    var $btn_work_recover = $('#btn_work_recover');
    var $btn_work_stop = $('#btn_work_stop');
    var $btn_work_download = $('#btn_work_download');
    var work_info = {};
    var current_work_id = "";
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;

    getWorkList();
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $("#work_create_modal").on("hidden.bs.modal", resetModal);
    $btn_work_create.bind('click', createWork);
    $btn_work_delete.bind('click', deleteWork);
    $btn_work_rerun.bind('click', rerunWork);
    $btn_work_recover.bind('click', recoverWork);
    $btn_work_stop.bind('click', stopWork);

    function showCreate() {
        $('#work_create_modal').modal('show');
    }

    async function createWork() {
        var data = {};
        data.workflow_id = $('input#workflow_id').val();
        data.name = $('input#work_name').val();
        var input_data = $('textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#work_create_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/work/create",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getWorkList(work_id) {
        var url = "http://" + manager_host + "/work/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
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
                $table_header_tr.append(getHeaderTR('work_id', 'work id', 'work id'));
                $table_header_tr.append(getHeaderTR('name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('workflow_id', 'workflow id', 'workflow id'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('start_at', 'start at', 'start at'));
                $table_header_tr.append(getHeaderTR('end_at', 'end at', 'end at'));
                $table_header_tr.append(getHeaderTR('stage', 'stage', 'stage'));
                $table_header_tr.append(getHeaderTR('status', 'status', 'status'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "work_id",
                    "name",
                    "workflow_id",
                    "create_at",
                    "start_at",
                    "end_at",
                    "stage",
                    "status",
                    "operation"
                ];
                work_info = {};
                data.works.forEach(function (value, index, arrays) {
                    work_info[value["work_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["work_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-rerun" onclick="this.blur();"><span class="oi oi-play-circle" title="rerun" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["work_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-recover" onclick="this.blur();"><span class="oi oi-circle-check" title="recover" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["work_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-stop" onclick="this.blur();"><span class="oi oi-media-stop" title="stop" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["work_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["work_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'work_id' || col == 'workflow_id') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                        } else if (col == 'name') {
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
                $(".btn-rerun").bind('click', showWorkRerun);
                $(".btn-recover").bind('click', showWorkRecover);
                $(".btn-stop").bind('click', showWorkStop);
                $(".btn-delete").bind('click', showWorkDelete);
                $(".btn-detail").bind('click', showWorkDetail);

                if (work_id) {
                    var info = {};
                    if (work_info[work_id]) {
                        info = work_info[work_id];
                    }
                    document.getElementById("work_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#work_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#work_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshWorkInfo(event) {
        $('#work_info_refresh').attr("disabled", "disabled");
        var work_id = event.data.work_id;
        getWorkList(work_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getWorkList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getWorkList();
    }

    function showWorkRerun() {
        current_work_id = $(this).attr("id");
        $('#work_rerun_modal').modal('show');
    }

    async function rerunWork() {
        var data = {"work_id": current_work_id};
        $('#work_rerun_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/work/rerun",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkRecover() {
        current_work_id = $(this).attr("id");
        $('#work_recover_modal').modal('show');
    }

    async function recoverWork() {
        var data = {"work_id": current_work_id};
        $('#work_recover_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/work/recover",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkStop() {
        current_work_id = $(this).attr("id");
        $('#work_stop_modal').modal('show');
    }

    async function stopWork() {
        var data = {"work_id": current_work_id, "signal": -9};
        $('#work_stop_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/work/stop",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkDelete() {
        current_work_id = $(this).attr("id");
        $('#work_delete_modal').modal('show');
    }

    async function deleteWork() {
        $('#work_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/work/delete?work_id=" + current_work_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkDetail() {
        var work_id = $(this).attr("id");
        document.getElementById("work_info_json").textContent = JSON.stringify(work_info[work_id], undefined, 4);
        $('#work_info_refresh').bind('click', {"work_id": work_id}, refreshWorkInfo);
        $('#work_info_modal').modal('show');
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getWorkList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getWorkList();
    }

    function nextPage() {
        current_page++;
        getWorkList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("textarea").val("");
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
        if (is_in('workflow_id', keys)) {
            $('th#workflow_id').css("width", "10%");
            $('td#workflow_id').css("width", "10%");
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
        if (is_in('work_id', keys)) {
            var width = percent;
            $('th#work_id').css("width", width + "%");
            $('td#work_id').css("width", width + "%");
        }
    }
}