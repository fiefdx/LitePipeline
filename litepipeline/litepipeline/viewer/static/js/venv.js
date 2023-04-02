function venvInit (manager_host, user, token) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_search = $("#btn_search");
    var $btn_venv_create = $('#btn_venv_create');
    var $btn_venv_update = $('#btn_venv_update');
    var $btn_venv_download = $('#btn_venv_download');
    var $btn_venv_delete = $('#btn_venv_delete');
    var venv_info = {};
    var download_venv_id = '';
    var delete_venv_id = '';
    var filter_type = "";
    var filter_value = "";
    var current_page = 1;
    var current_page_size = 50;
    var host = window.location.host;

    getVenvList();
    $btn_refresh.bind('click', refreshPage);
    $btn_create.bind('click', showCreate);
    $btn_search.bind('click', search);
    $btn_venv_create.bind('click', createVenv);
    $(".custom-file-input").on("change", function() {
        var fileName = $(this).val().split("\\").pop();
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });
    $("#venv_create_modal").on("hidden.bs.modal", resetModal);
    $("#venv_update_modal").on("hidden.bs.modal", resetModal);
    $btn_venv_update.bind('click', updateVenv);
    $btn_venv_download.bind('click', downloadVenv);
    $btn_venv_delete.bind('click', deleteVenv);

    function showCreate() {
        $('#venv_create_modal').modal('show');
    }

    function createVenv() {
        var form = document.getElementById('form_create');
        var form_data = new FormData(form);
        $('#venv_create_modal').modal('hide');
        showWaitScreen();
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/venv/create",
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
                getVenvList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function getVenvList(venv_id) {
        var url = "http://" + manager_host + "/venv/list?offset=" + ((current_page - 1) * current_page_size) + "&limit=" + current_page_size;
        if (filter_type) {
            url += "&" + filter_type + "=" + filter_value;
        }
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
                $table_header_tr.append(getHeaderTR('venv_id', 'venv id', 'venv id'));
                $table_header_tr.append(getHeaderTR('name', 'name', 'name'));
                $table_header_tr.append(getHeaderTR('sha1', 'sha1', 'sha1'));
                $table_header_tr.append(getHeaderTR('create_at', 'create at', 'create at'));
                $table_header_tr.append(getHeaderTR('update_at', 'update at', 'update at'));
                $table_header_tr.append(getHeaderTR('operation', 'operation', 'operation'));
                var columns = [
                    "num",
                    "venv_id",
                    "name",
                    "sha1",
                    "create_at",
                    "update_at",
                    "operation"
                ];
                venv_info = {};
                data.venvs.forEach(function (value, index, arrays) {
                    venv_info[value["venv_id"]] = value;
                    var tr = '<tr id="table_item">';
                    for (var i=0; i<columns.length; i++) {
                        var col = columns[i];
                        if (col == 'num') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + ((current_page - 1) * current_page_size + index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["venv_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["venv_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-download" onclick="this.blur();"><span class="oi oi-arrow-circle-bottom" title="download" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["venv_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["venv_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'venv_id' || col == 'sha1') {
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
                $(".btn-update").bind('click', showVenvUpdate);
                $(".btn-download").bind('click', showVenvDownload);
                $(".btn-delete").bind('click', showVenvDelete);
                $(".btn-detail").bind('click', openVenvInfoPage);

                if (venv_id) {
                    var info = {};
                    if (venv_info[venv_id]) {
                        info = venv_info[venv_id];
                    }
                    document.getElementById("venv_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                generatePagination(current_page, current_page_size, 5, data.total);
                $('a.page-num').bind('click', changePage);
                $('a.previous-page').bind('click', previousPage);
                $('a.next-page').bind('click', nextPage);

                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#venv_info_refresh').removeAttr("disabled");
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
                $btn_refresh.removeAttr("disabled");
                $('#venv_info_refresh').removeAttr("disabled");
            }
        });
    }

    function refreshVenvInfo(event) {
        $('#venv_info_refresh').attr("disabled", "disabled");
        var venv_id = event.data.venv_id;
        getVenvList(venv_id);
    }

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getVenvList();
    }

    function search() {
        filter_type = $('#filter').val();
        filter_value = $('input#filter_input').val();
        current_page = 1;
        getVenvList();
    }

    function showVenvUpdate() {
        var venv_id = $(this).attr("id");
        var info = venv_info[venv_id];
        $('#form_update input#venv_id').val(venv_id);
        $('#form_update input#venv_name').val(info.name);
        $('#form_update textarea#venv_description').val(info.description);
        $('#venv_update_modal').modal('show');
    }

    async function updateVenv() {
        var form = document.getElementById('form_update');
        var form_data = new FormData(form);
        $('#venv_update_modal').modal('hide');
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
                getVenvList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function showVenvDownload() {
        download_venv_id = $(this).attr("id");
        $('#venv_download_modal').modal('show');
    }

    async function downloadVenv() {
        var url = "http://" + manager_host + "/venv/download?venv_id=" + download_venv_id;
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
                $('#venv_download_modal').modal('hide');
            }).catch((err) => {
                $('#venv_download_modal').modal('hide');
                console.log(err);
            });
        }).catch((err) => {
            $('#venv_download_modal').modal('hide');
            console.log(err);
        });
    }

    function showVenvDelete() {
        delete_venv_id = $(this).attr("id");
        $('#venv_delete_modal').modal('show');
    }

    async function deleteVenv() {
        $('#venv_delete_modal').modal('hide');
        showWaitScreen();
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/venv/delete?venv_id=" + delete_venv_id,
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
                getVenvList();
            },
            error: function() {
                showWarningToast("error", "request service failed");
            }
        });
    }

    function openVenvInfoPage() {
        var venv_id = $(this).attr("id");
        var url = "http://" + host + "/venv/" + venv_id;
        var win = window.open(url, '_blank');
        win.focus();
    }

    function changePage() {
        current_page = Number($(this)[0].innerText);
        getVenvList();
    }

    function previousPage() {
        current_page--;
        if (current_page < 1) {
            current_page = 1;
        }
        getVenvList();
    }

    function nextPage() {
        current_page++;
        getVenvList();
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
        if (is_in('venv_id', keys)) {
            var width = percent;
            $('th#venv_id').css("width", width + "%");
            $('td#venv_id').css("width", width + "%");
        }
    }
}