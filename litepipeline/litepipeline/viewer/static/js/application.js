function applicationInit (manager_host) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_app_create = $('#btn_app_create');
    var $btn_app_update = $('#btn_app_update');
    var $btn_app_download = $('#btn_app_download');
    var $btn_app_delete = $('#btn_app_delete');
    var application_info = {};
    var download_application_id = '';
    var delete_application_id = '';
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;
    var host = window.location.host;

    getAppList();
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $btn_app_create.bind('click', createApp);
    $(".custom-file-input").on("change", function() {
        var fileName = $(this).val().split("\\").pop();
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });
    $("#app_create_modal").on("hidden.bs.modal", resetModal);
    $("#app_update_modal").on("hidden.bs.modal", resetModal);
    $btn_app_update.bind('click', updateApp);
    $btn_app_download.bind('click', downloadApp);
    $btn_app_delete.bind('click', deleteApp);

    function showCreate() {
        $('#app_create_modal').modal('show');
    }

    function createApp() {
        var form = document.getElementById('form_create');
        var form_data = new FormData(form);
        $('#app_create_modal').modal('hide');
        showWaitScreen();
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/app/create",
            data: form_data,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getAppList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getAppList(application_id) {
        var url = "http://" + manager_host + "/app/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
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
                $table_header_tr.append(getHeaderTR('application_id', 'application id', 'application id'));
                $table_header_tr.append(getHeaderTR('name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('sha1', 'sha1', 'sha1'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('update_at', 'update at', 'update at'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
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
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-download" onclick="this.blur();"><span class="oi oi-arrow-circle-bottom" title="download" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'application_id' || col == 'sha1') {
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
                $(".btn-update").bind('click', showAppUpdate);
                $(".btn-download").bind('click', showAppDownload);
                $(".btn-delete").bind('click', showAppDelete);
                $(".btn-detail").bind('click', openAppInfoPage);

                if (application_id) {
                    var info = {};
                    if (application_info[application_id]) {
                        info = application_info[application_id];
                    }
                    document.getElementById("app_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#app_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#app_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshAppInfo(event) {
        $('#app_info_refresh').attr("disabled", "disabled");
        var application_id = event.data.application_id;
        getAppList(application_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getAppList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getAppList();
    }

    function showAppUpdate() {
        var application_id = $(this).attr("id");
        var info = application_info[application_id];
        $('#form_update input#application_id').val(application_id);
        $('#form_update input#application_name').val(info.name);
        $('#form_update textarea#application_description').val(info.description);
        $('#app_update_modal').modal('show');
    }

    async function updateApp() {
        var form = document.getElementById('form_update');
        var form_data = new FormData(form);
        $('#app_update_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/app/update",
            data: form_data,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getAppList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showAppDownload() {
        download_application_id = $(this).attr("id");
        $('#app_download_modal').modal('show');
    }

    function downloadApp() {
        var url = "http://" + manager_host + "/app/download?app_id=" + download_application_id;
        var win = window.open(url, '_blank');
        win.focus();
        $('#app_download_modal').modal('hide');
    }

    function showAppDelete() {
        delete_application_id = $(this).attr("id");
        $('#app_delete_modal').modal('show');
    }

    async function deleteApp() {
        $('#app_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/app/delete?app_id=" + delete_application_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getAppList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function openAppInfoPage() {
        var application_id = $(this).attr("id");
        var url = "http://" + host + "/application/" + application_id;
        var win = window.open(url, '_blank');
        win.focus();
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getAppList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getAppList();
    }

    function nextPage() {
        current_page++;
        getAppList();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("input:file").val(null);
        $("#" + e.target.id).find(".custom-file-label").html("Choose file");
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
}