function applicationInit (manager_host) {
	var $table_header = $(".header-fixed > thead");
    var $table_header_tr = $(".header-fixed > thead > tr");
    var $table_body = $(".header-fixed > tbody");
    var scrollBarSize = getBrowserScrollSize();
    var $btn_refresh = $("#btn_refresh");
    var $btn_create = $("#btn_create");
    var $btn_app_create = $('#btn_app_create');
    var $btn_app_update = $('#btn_app_update');
    var $btn_app_download = $('#btn_app_download');
    var $btn_app_delete = $('#btn_app_delete');
    var application_info = {};
    var download_application_id = '';
    var delete_application_id = '';

    getAppList();
    $btn_refresh.bind('click', getAppList);
    $btn_create.bind('click', showCreate);
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
        $('#loading_modal').modal('show');
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/app/create",
            data: form_data,
            contentType: false,
            processData: false,
            success: function() {
                getAppList();
            }
        });
    }

    function getAppList(application_id) {
        $.ajax({
            dataType: "json",
            url: "http://" + manager_host + "/app/list",
            success: function(data) {
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
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">&nbsp;' + (index + 1) + '</div></div></td>';
                        } else if (col == 'operation') {
                            tr += '<td id="' + col + '"><div class="outer"><div class="inner">';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-update" onclick="this.blur();"><span class="oi oi-arrow-circle-top" title="update" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-download" onclick="this.blur();"><span class="oi oi-arrow-circle-bottom" title="download" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-delete" onclick="this.blur();"><span class="oi oi-circle-x" title="delete" aria-hidden="true"></span></button>';
                            tr += '<button id="' + value["application_id"] + '" type="button" class="btn btn-secondary btn-sm btn-operation btn-detail" onclick="this.blur();"><span class="oi oi-spreadsheet" title="detail" aria-hidden="true"></span></button>';
                            tr += '</div></div></td>';
                        } else if (col == 'application_id' || col == 'sha1') {
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
                $(".btn-update").bind('click', showAppUpdate);
                $(".btn-download").bind('click', showAppDownload);
                $(".btn-delete").bind('click', showAppDelete);
                $(".btn-detail").bind('click', showAppDetail);

                if (application_id) {
                    var info = {};
                    if (application_info[application_id]) {
                        info = application_info[application_id];
                    }
                    document.getElementById("app_info_json").textContent = JSON.stringify(info, undefined, 4);
                }

                $('#loading_modal').modal('hide');
            }
        });
    }

    function getHeaderTR(id, title, value) {
        return '<th id="' + id + '" title="' + title + '"><div class="outer"><div class="inner">&nbsp;' + value + '</div></div></th>';
    }

    function refreshAppInfo(event) {
        var application_id = event.data.application_id;
        getAppList(application_id);
    }

    function showAppUpdate() {
        var application_id = $(this).attr("id");
        $('input#application_id').val(application_id);
        $('#app_update_modal').modal('show');
    }

    async function updateApp() {
        var form = document.getElementById('form_update');
        var form_data = new FormData(form);
        $('#app_update_modal').modal('hide');
        $('#loading_modal').modal('show');
        await sleep(1000);
        $.ajax({
            type: "POST",
            url: "http://" + manager_host + "/app/update",
            data: form_data,
            contentType: false,
            processData: false,
            success: function() {
                getAppList();
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
        $('#loading_modal').modal('show');
        await sleep(1000);
        $.ajax({
            type: "DELETE",
            url: "http://" + manager_host + "/app/delete?app_id=" + delete_application_id,
            contentType: false,
            processData: false,
            success: function() {
                getAppList();
            }
        });
    }

    function showAppDetail() {
        var application_id = $(this).attr("id");
        document.getElementById("app_info_json").textContent = JSON.stringify(application_info[application_id], undefined, 4);
        $('#app_info_refresh').bind('click', {"application_id": application_id}, refreshAppInfo);
        $('#app_info_modal').modal('show');
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("input:file").val(null);
        $("#" + e.target.id).find(".custom-file-label").html("");
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

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}