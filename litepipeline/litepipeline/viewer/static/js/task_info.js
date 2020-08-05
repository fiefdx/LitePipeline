function TaskInfoInit (manager_host, task_id) {
    var $btn_rerun = $('#btn-rerun');
    var $btn_recover = $('#btn-recover');
    var $btn_stop = $('#btn-stop');
    var $btn_download = $('#btn-download');
    var $btn_task_download = $('#btn-task-download');
    var $btn_refresh = $('#btn-refresh');
    var task_info = {};

    getTaskInfo();
    $btn_download.bind('click', showTaskDownload);
    $btn_task_download.bind('click', downloadTask);
    $btn_refresh.bind('click', refreshPage);

    function getTaskInfo(with_history) {
        var url = "http://" + manager_host + "/task/info?task_id=" + task_id;
        $.ajax({
            dataType: "json",
            url: url,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    task_info = data.task_info;
                    document.getElementById("task-info-json").textContent = JSON.stringify(data.task_info, undefined, 4);
                    if (data.task_running_info) {
                        document.getElementById("task-running-info-json").textContent = JSON.stringify(data.task_running_info, undefined, 4);
                    }
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

    function showTaskDownload() {
        $("select#action-name").empty();
        var actions = task_info.result;
        for (var action_name in actions) {
            $("select#action-name").append(
                '<option value="' + action_name + '">' + action_name + '</option>'
            );
        }
        $('#task-download-modal').modal('show');
    }

    async function downloadTask() {
        var name = $("select#action-name").val();
        var data = {"task_id": task_id, "name": name, "force": true};
        $('#task-download-modal').modal('hide');
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

    function refreshPage() {
        $btn_refresh.attr("disabled", "disabled");
        getTaskInfo();
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("input:file").val(null);
        $("#" + e.target.id).find(".custom-file-label").html("Choose file");
        $("#" + e.target.id).find("textarea").val("");
    }
}