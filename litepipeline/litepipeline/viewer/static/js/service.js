function serviceInit (manager_host) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_service_create = $('#btn_service_create');
    var $btn_service_update = $('#btn_service_update');
    var $btn_service_delete = $('#btn_service_delete');
    var service_info = {};
    var current_service_id = "";
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;

    getServiceList();
    $("#service_create_modal").on("hidden.bs.modal", resetModal);
    $("#service_update_modal").on("hidden.bs.modal", resetModal);
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $btn_service_create.bind('click', createService);
    $btn_service_update.bind('click', updateService);
    $btn_service_delete.bind('click', deleteService);

    function showCreate() {
        $('#service_create_modal').modal('show');
    }

    async function createService() {
        var data = {};
        data.name = $('#form_create input#service_name').val();
        data.app_id = $('#form_create input#app_id').val();
        data.signal = Number($('#form_create select#stop_signal').val());
        data.enable = $('#form_create input#enable').is(":checked");
        data.description = $('#form_create textarea#description').val();
        var input_data = $('#form_create textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#service_create_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/service/create",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getServiceList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getServiceList(service_id) {
        var url = "http://" + manager_host + "/service/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size + "&" + filter_type + "=" + filter_value;
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
                $table_header_tr.append(getHeaderTR('service_id', 'service id', 'service id'));
                $table_header_tr.append(getHeaderTR('name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('application_id', 'application id', 'application id'));
                $table_header_tr.append(getHeaderTR('task_id', 'task id', 'task id'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('update_at', 'update at', 'update at'));
                $table_header_tr.append(getHeaderTR('stage', 'stage', 'stage'));
                $table_header_tr.append(getHeaderTR('status', 'status', 'status'));
                $table_header_tr.append(getHeaderTR('enable', 'enable', 'enable'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "service_id",
                    "name",
                    "application_id",
                    "task_id",
                    "create_at",
                    "update_at",
                    "stage",
                    "status",
                    "enable",
                    "operation"
                ];
                service_info = {};
                data.services.forEach(function (value, index, arrays) {
                    service_info[value["service_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["service_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["service_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["service_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'service_id' || col == 'application_id' || col == 'task_id') {
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
                $(".btn-update").bind('click', showServiceUpdate);
                $(".btn-delete").bind('click', showServiceDelete);
                $(".btn-detail").bind('click', showServiceDetail);

                if (service_id) {
                    var info = {};
                    if (service_info[service_id]) {
                        info = service_info[service_id];
                    }
                    document.getElementById("service_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#service_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#service_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshServiceInfo(event) {
        $('#service_info_refresh').attr("disabled", "disabled");
        var service_id = event.data.service_id;
        getServiceList(service_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getServiceList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getServiceList();
    }

    function showServiceUpdate() {
        current_service_id = $(this).attr("id");
        var info = service_info[current_service_id];
        $('#form_update input#service_name').val(info.name);
        $('#form_update input#app_id').val(info.application_id);
        $('#form_update textarea#description').val(info.description);
        $('#form_update select#stop_signal').val(info.signal);
        $('#form_update input#enable').prop("checked", info.enable);
        $('#form_update textarea#input_data').val(JSON.stringify(info.input_data), undefined, 4);
        $('#service_update_modal').modal('show');
    }

    async function updateService() {
        var data = {};
        data.service_id = current_service_id;
        var name = $('#form_update input#service_name').val();
        if (name) {
            data.name = name;
        }
        data.app_id = $('#form_update input#app_id').val();
        data.description = $('#form_update textarea#description').val();
        data.signal = Number($('#form_update select#stop_signal').val());
        data.enable = $('#form_update input#enable').is(":checked");
        var input_data = $('#form_update textarea#input_data').val();
        if (input_data) {
            data.input_data = JSON.parse(input_data);
        }
        $('#service_update_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/service/update",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getServiceList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showServiceDelete() {
        current_service_id = $(this).attr("id");
        $('#service_delete_modal').modal('show');
    }

    async function deleteService() {
        $('#service_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/service/delete?service_id=" + current_service_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getServiceList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showServiceDetail() {
        var service_id = $(this).attr("id");
        document.getElementById("service_info_json").textContent = JSON.stringify(service_info[service_id], undefined, 4);
        $('#service_info_refresh').bind('click', {"service_id": service_id}, refreshServiceInfo);
        $('#service_info_modal').modal('show');
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getServiceList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getServiceList();
    }

    function nextPage() {
        current_page++;
        getServiceList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("textarea").val("");
        $("#" + e.target.id).find('select#stop_signal').val(-9);
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
        if (is_in('stage', keys)) {
            $('th#stage').css("width", "6%");
            $('td#stage').css("width", "6%");
            percent -= 6.0;
        }
        if (is_in('status', keys)) {
            $('th#status').css("width", "6%");
            $('td#status').css("width", "6%");
            percent -= 6.0;
        }
        if (is_in('enable', keys)) {
            $('th#enable').css("width", "3%");
            $('td#enable').css("width", "3%");
            percent -= 3.0;
        }
        if (is_in('service_id', keys)) {
            var width = percent;
            $('th#service_id').css("width", width + "%");
            $('td#service_id').css("width", width + "%");
        }
    }
}