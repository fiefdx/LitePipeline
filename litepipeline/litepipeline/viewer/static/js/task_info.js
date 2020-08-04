function TaskInfoInit (manager_host, task_id) {
    var $btn_download = $('#btn-download');
    var $btn_refresh = $('#btn-refresh');

    getTaskInfo();
    // $btn_download.bind('click', showAppDownload);
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
                    document.getElementById("task-info-json").textContent = JSON.stringify(data.task_info, undefined, 4);
                    if (data.task_running_info) {
                        document.getElementById("task-running-info-json").textContent = JSON.stringify(data.task_running_info, undefined, 4);
                    }
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
        getTaskInfo(true);
    }

    function resetModal(e) {
        $("#" + e.target.id).find("input:text").val("");
        $("#" + e.target.id).find("input:file").val(null);
        $("#" + e.target.id).find(".custom-file-label").html("Choose file");
        $("#" + e.target.id).find("textarea").val("");
    }
}