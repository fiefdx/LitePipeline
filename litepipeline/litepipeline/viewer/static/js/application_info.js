function applicationInfoInit (manager_host, application_id) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_update = $('#btn-update');
    var $btn_download = $('#btn-download');
    var $btn_refresh = $('#btn-refresh');
    var $btn_app_update = $('#btn-app-update');
    var $btn_app_download = $('#btn-app-download');
    var $btn_app_history_download = $('#btn-app-history-download');
    var $btn_app_history_activate = $('#btn-app-history-activate');
    var $btn_app_history_delete = $('#btn-app-history-delete');
    var current_page = 1;
    var current_page_size = 10;
    var app_info = {};
    var app_histories = {};
    var download_history_id = '';
    var delete_history_id = '';
    var activate_history_id = '';

    getAppInfo(true);
    $btn_update.bind('click', showAppUpdate);
    $btn_download.bind('click', showAppDownload);
    $btn_refresh.bind('click', refreshPage);
    $(".custom-file-input").on("change", function() {
        var fileName = $(this).val().split("\\").pop();
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });
    $("#app-update-modal").on("hidden.bs.modal", resetModal);
    $btn_app_update.bind('click', updateApp);
    $btn_app_download.bind('click', downloadApp);
    $btn_app_history_download.bind('click', downloadAppHistory);
    $btn_app_history_activate.bind('click', activateAppHistory);
    $btn_app_history_delete.bind('click', deleteAppHistory);

    function getAppInfo(with_history) {
        var url = "http://" + manager_host + "/app/info?app_id=" + application_id + "&config=true";
        $.ajax({
            dataType: "json",
            url: url,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    app_info = data.app_info;
                    document.getElementById("app-info-json").textContent = JSON.stringify(data.app_info, undefined, 4);
                    document.getElementById("app-config-json").textContent = JSON.stringify(data.app_config, undefined, 4);
                }

                if (with_history) {
                    getAppHistory();
                }

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
            }
        });
    }

    function getAppHistory() {
        var url = "http://" + manager_host + "/app/history/list?app_id=" + application_id + "&offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
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
                $table_header_tr.append(getHeaderTR('id', 'history id', 'history id'));
                $table_header_tr.append(getHeaderTR('sha1', 'sha1', 'sha1'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "id",
                    "sha1",
                    "create_at",
                    "operation"
                ];
                app_histories = {};
                data.app_histories.forEach(function (value, index, arrays) {
                    app_histories[value["id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-download" onclick="this.blur();"><span class="oi oi-arrow-circle-bottom" title="download" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-activate" onclick="this.blur();"><span class="oi oi-task" title="activate" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'id' || col == 'sha1') {
                            if (app_info["sha1"] == value[col]) {
                                tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre history-current">' + value[col] + '</span></div></div></td>';
                            } else {
                                tr += '<td id="' + col + '"><div class="outer"><div class="inner"><span class="span-pre">' + value[col] + '</span></div></div></td>';
                            }
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
                $(".btn-download").bind('click', showAppHistoryDownload);
                $(".btn-activate").bind('click', showAppHistoryActivate);
                $(".btn-delete").bind('click', showAppHistoryDelete);
                $(".btn-detail").bind('click', showAppHistoryDetail);

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
            }
        });
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getAppHistory();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getAppHistory();
    }

    function nextPage() {
        current_page++;
        getAppHistory();
    }

    function showAppUpdate() {
        $('#form-update input#application-id').val(application_id);
        $('#form-update input#application-name').val(app_info.name);
        $('#form-update textarea#application-description').val(app_info.description);
        $('#app-update-modal').modal('show');
    }

    async function updateApp() {
        var form = document.getElementById('form-update');
        var form_data = new FormData(form);
        $('#app-update-modal').modal('hide');
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
                getAppInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showAppDownload() {
        $('#app-download-modal').modal('show');
    }

    function downloadApp() {
        var url = "http://" + manager_host + "/app/download?app_id=" + application_id;
        var win = window.open(url, '_blank');
        win.focus();
        $('#app-download-modal').modal('hide');
    }

    function showAppHistoryDownload() {
        download_history_id = $(this).attr("id");
        $('#app-history-download-modal').modal('show');
    }

    function downloadAppHistory() {
        var url = "http://" + manager_host + "/app/download?app_id=" + application_id + "&sha1=" + app_histories[download_history_id].sha1;
        var win = window.open(url, '_blank');
        win.focus();
        $('#app-history-download-modal').modal('hide');
    }

    function showAppHistoryActivate() {
        activate_history_id = $(this).attr("id");
        $('#app-history-activate-modal').modal('show');
    }

    async function activateAppHistory() {
        $('#app-history-activate-modal').modal('hide');
        showWaitScreen();
        var data = {};
        data.app_id = application_id;
        data.history_id = activate_history_id;
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/app/history/activate",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getAppInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showAppHistoryDelete() {
        delete_history_id = $(this).attr("id");
        $('#app-history-delete-modal').modal('show');
    }

    async function deleteAppHistory() {
        $('#app-history-delete-modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/app/history/delete?app_id=" + application_id + "&history_id=" + delete_history_id,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getAppInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showAppHistoryDetail() {
        var history_id = $(this).attr("id");
        var url = "http://" + manager_host + "/app/history/info?app_id=" + application_id + "&history_id=" + history_id + "&config=true";
        $.ajax({
            dataType: "json",
            url: url,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    document.getElementById("history-info-json").textContent = JSON.stringify(data.history_info, undefined, 4);
                    document.getElementById("history-config-json").textContent = JSON.stringify(data.history_config, undefined, 4);
                    $('#history-info-modal').modal('show');
                }

                hideWaitScreen();
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
            }
        });
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getAppInfo(true);
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
        if (is_in('create_at', keys)) {
            $('th#create_at').css("width", "25%");
            $('td#create_at').css("width", "25%");
            percent -= 25.0;
        }
        if (is_in('sha1', keys)) {
            $('th#sha1').css("width", "30%");
            $('td#sha1').css("width", "30%");
            percent -= 30.0;
        }
        if (is_in('operation', keys)) {
            $('th#operation').css("width", "8%");
            $('td#operation').css("width", "8%");
            percent -= 8.0;
        }
        if (is_in('id', keys)) {
            var width = percent;
            $('th#id').css("width", width + "%");
            $('td#id').css("width", width + "%");
        }
    }
}