function venvInfoInit (manager_host, venv_id, user, token) {
    var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_update = $('#btn-update');
    var $btn_download = $('#btn-download');
    var $btn_refresh = $('#btn-refresh');
    var $btn_venv_update = $('#btn-venv-update');
    var $btn_venv_download = $('#btn-venv-download');
    var $btn_venv_history_download = $('#btn-venv-history-download');
    var $btn_venv_history_activate = $('#btn-venv-history-activate');
    var $btn_venv_history_delete = $('#btn-venv-history-delete');
    var current_page = 1;
    var current_page_size = 10;
    var venv_info = {};
    var venv_histories = {};
    var download_history_id = '';
    var delete_history_id = '';
    var activate_history_id = '';

    getVenvInfo(true);
    $btn_update.bind('click', showVenvUpdate);
    $btn_download.bind('click', showVenvDownload);
    $btn_refresh.bind('click', refreshPage);
    $(".custom-file-input").on("change", function() {
        var fileName = $(this).val().split("\\").pop();
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });
    $("#venv-update-modal").on("hidden.bs.modal", resetModal);
    $btn_venv_update.bind('click', updateVenv);
    $btn_venv_download.bind('click', downloadVenv);
    $btn_venv_history_download.bind('click', downloadVenvHistory);
    $btn_venv_history_activate.bind('click', activateVenvHistory);
    $btn_venv_history_delete.bind('click', deleteVenvHistory);

    function getVenvInfo(with_history) {
        var url = "http://" + manager_host + "/venv/info?venv_id=" + venv_id;
        $.ajax({
            dataType: "json",
            url: url,
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    venv_info = data.venv_info;
                    document.getElementById("venv-info-json").textContent = JSON.stringify(data.venv_info, undefined, 4);
                }

                if (with_history) {
                    getVenvHistory();
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

    function getVenvHistory() {
        var url = "http://" + manager_host + "/venv/history/list?venv_id=" + venv_id + "&offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
        $.ajax({
            dataType: "json",
            url: url,
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
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
                venv_histories = {};
                data.venv_histories.forEach(function (value, index, arrays) {
                    venv_histories[value["id"]] = value;
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
                            if (venv_info["sha1"] == value[col]) {
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
                $(".btn-download").bind('click', showVenvHistoryDownload);
                $(".btn-activate").bind('click', showVenvHistoryActivate);
                $(".btn-delete").bind('click', showVenvHistoryDelete);
                $(".btn-detail").bind('click', showVenvHistoryDetail);

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
        getVenvHistory();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getVenvHistory();
    }

    function nextPage() {
        current_page++;
        getVenvHistory();
    }

    function showVenvUpdate() {
        $('#form-update input#venv-id').val(venv_id);
        $('#form-update input#venv-name').val(venv_info.name);
        $('#form-update textarea#venv-description').val(venv_info.description);
        $('#venv-update-modal').modal('show');
    }

    async function updateVenv() {
        var form = document.getElementById('form-update');
        var form_data = new FormData(form);
        $('#venv-update-modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/venv/update",
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
            data: form_data,
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getVenvInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showVenvDownload() {
        $('#venv-download-modal').modal('show');
    }

    async function downloadVenv() {
        var url = "http://" + manager_host + "/venv/download?venv_id=" + venv_id;
        fetch(url, {headers: {'user': user, 'token': token}}
        ).then((response) => {
            // console.log(...response.headers);
            const name = response.headers.get("Content-Disposition")
                                         .split(';')
                                         .find(n => n.includes('filename='))
                                         .replace('filename=', '')
                                         .trim();
            response.blob().then((data) => {
                var _url = window.URL.createObjectURL(data);
                var a = document.createElement("a");
                document.body.appendChild(a);
                a.style = "display: none";
                a.href = _url;
                a.download = name;
                a.click();
                window.URL.revokeObjectURL(_url);
                $('#venv-download-modal').modal('hide');
            }).catch((err) => {
                $('#venv-download-modal').modal('hide');
                console.log(err);
            });
        }).catch((err) => {
            $('#venv-download-modal').modal('hide');
            console.log(err);
        });
    }

    function showVenvHistoryDownload() {
        download_history_id = $(this).attr("id");
        $('#venv-history-download-modal').modal('show');
    }

    async function downloadVenvHistory() {
        var url = "http://" + manager_host + "/venv/download?venv_id=" + venv_id + "&sha1=" + venv_histories[download_history_id].sha1;
        fetch(url, {headers: {'user': user, 'token': token}}
        ).then((response) => {
            // console.log(...response.headers);
            const name = response.headers.get("Content-Disposition")
                                         .split(';')
                                         .find(n => n.includes('filename='))
                                         .replace('filename=', '')
                                         .trim();
            response.blob().then((data) => {
                var _url = window.URL.createObjectURL(data);
                var a = document.createElement("a");
                document.body.appendChild(a);
                a.style = "display: none";
                a.href = _url;
                a.download = name;
                a.click();
                window.URL.revokeObjectURL(_url);
                $('#venv-history-download-modal').modal('hide');
            }).catch((err) => {
                $('#venv-history-download-modal').modal('hide');
                console.log(err);
            });
        }).catch((err) => {
            $('#venv-history-download-modal').modal('hide');
            console.log(err);
        });
    }

    function showVenvHistoryActivate() {
        activate_history_id = $(this).attr("id");
        $('#venv-history-activate-modal').modal('show');
    }

    async function activateVenvHistory() {
        $('#venv-history-activate-modal').modal('hide');
        showWaitScreen();
        var data = {};
        data.venv_id = venv_id;
        data.history_id = activate_history_id;
        await sleep(1000);
        $.ajax({
            type: "PUT",
            url: "http://" + manager_host + "/venv/history/activate",
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
            data: JSON.stringify(data),
            dataType: "json",
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getVenvInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showVenvHistoryDelete() {
        delete_history_id = $(this).attr("id");
        $('#venv-history-delete-modal').modal('show');
    }

    async function deleteVenvHistory() {
        $('#venv-history-delete-modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/venv/history/delete?venv_id=" + venv_id + "&history_id=" + delete_history_id,
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
            contentType: false,
            processData: false,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                }
                getVenvInfo(true);
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showVenvHistoryDetail() {
        var history_id = $(this).attr("id");
        var url = "http://" + manager_host + "/venv/history/info?venv_id=" + venv_id + "&history_id=" + history_id;
        $.ajax({
            dataType: "json",
            url: url,
            beforeSend: function(request) {
                request.setRequestHeader("user", user);
                request.setRequestHeader("token", token);
            },
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    document.getElementById("history-info-json").textContent = JSON.stringify(data.history_info, undefined, 4);
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
        getVenvInfo(true);
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