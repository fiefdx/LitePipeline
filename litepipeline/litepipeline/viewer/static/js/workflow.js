function workflowInit (manager_host) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_workflow_create = $('#btn_workflow_create');
    var $btn_workflow_update = $('#btn_workflow_update');
    var $btn_workflow_delete = $('#btn_workflow_delete');
    var workflow_info = {};
    var delete_workflow_id = '';
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;

    getWorkflowList();
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $btn_workflow_create.bind('click', createWorkflow);
    $("#workflow_create_modal").on("hidden.bs.modal", resetModal);
    $("#workflow_update_modal").on("hidden.bs.modal", resetModal);
    $btn_workflow_update.bind('click', updateWorkflow);
    $btn_workflow_delete.bind('click', deleteWorkflow);

    function showCreate() {
        $('#workflow_create_modal').modal('show');
    }

    async function createWorkflow() {
        var data = {};
        data.name = $('#form_create input#workflow_name').val();
        var configuration = $('#form_create textarea#workflow_configuration').val()
        if (configuration) {
            configuration = JSON.parse(configuration);
        } else {
            configuration = {};
        }
        data.configuration = configuration;
        data.description = $('#form_create textarea#workflow_description').val();
        data.enable = $('#form_create input#enable').is(":checked");
        $('#workflow_create_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/workflow/create",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkflowList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getWorkflowList(workflow_id) {
        var url = "http://" + manager_host + "/workflow/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
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
                $table_header_tr.append(getHeaderTR('workflow_id', 'workflow id', 'workflow id'));
                $table_header_tr.append(getHeaderTR('name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('update_at', 'update at', 'update at'));
                $table_header_tr.append(getHeaderTR('enable', 'enable', 'enable'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "workflow_id",
                    "name",
                    "create_at",
                    "update_at",
                    "enable",
                    "operation"
                ];
                workflow_info = {};
                data.workflows.forEach(function (value, index, arrays) {
                    workflow_info[value["workflow_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["workflow_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["workflow_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["workflow_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'workflow_id') {
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
                $(".btn-update").bind('click', showWorkflowUpdate);
                $(".btn-delete").bind('click', showWorkflowDelete);
                $(".btn-detail").bind('click', showWorkflowDetail);

                if (workflow_id) {
                    var info = {};
                    if (workflow_info[workflow_id]) {
                        info = workflow_info[workflow_id];
                    }
                    document.getElementById("workflow_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#workflow_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#workflow_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshWorkflowInfo(event) {
        $('#workflow_info_refresh').attr("disabled", "disabled");
        var workflow_id = event.data.workflow_id;
        getWorkflowList(workflow_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getWorkflowList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getWorkflowList();
    }

    function showWorkflowUpdate() {
        var workflow_id = $(this).attr("id");
        var info = workflow_info[workflow_id];
        $('#form_update input#workflow_id').val(workflow_id);
        $('#form_update input#workflow_name').val(info.name);
        $('#form_update textarea#workflow_configuration').val(JSON.stringify(info.configuration, undefined, 4));
        $('#form_update textarea#workflow_description').val(info.description);
        $('#form_update input#enable').prop("checked", info.enable);
        $('#workflow_update_modal').modal('show');
    }

    async function updateWorkflow() {
        var data = {};
        data.workflow_id = $('#form_update input#workflow_id').val();
        data.name = $('#form_update input#workflow_name').val();
        var configuration = $('#form_update textarea#workflow_configuration').val();
        if (configuration) {
            configuration = JSON.parse(configuration);
        } else {
            configuration = {};
        }
        data.configuration = configuration;
        data.description = $('#form_update textarea#workflow_description').val();
        data.enable = $('#form_update input#enable').is(":checked");
        $('#workflow_update_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/workflow/update",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkflowList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkflowDelete() {
        delete_workflow_id = $(this).attr("id");
        $('#workflow_delete_modal').modal('show');
    }

    async function deleteWorkflow() {
        $('#workflow_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/workflow/delete?workflow_id=" + delete_workflow_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getWorkflowList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showWorkflowDetail() {
        var workflow_id = $(this).attr("id");
        document.getElementById("workflow_info_json").textContent = JSON.stringify(workflow_info[workflow_id], undefined, 4);
        $('#workflow_info_refresh').bind('click', {"workflow_id": workflow_id}, refreshWorkflowInfo);
        $('#workflow_info_modal').modal('show');
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getWorkflowList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getWorkflowList();
    }

    function nextPage() {
        current_page++;
        getWorkflowList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("input:file").val(null);
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
        if (is_in('enable', keys)) {
            $('th#enable').css("width", "3%");
            $('td#enable').css("width", "3%");
            percent -= 3.0;
        }
        if (is_in('operation', keys)) {
            $('th#operation').css("width", "8%");
            $('td#operation').css("width", "8%");
            percent -= 8.0;
        }
        if (is_in('workflow_id', keys)) {
            var width = percent;
            $('th#workflow_id').css("width", width + "%");
            $('td#workflow_id').css("width", width + "%");
        }
    }
}