function applicationInfoInit (manager_host, application_id) {
    var $btn_update = $('#btn-update');
    var $btn_download = $('#btn-download');
    var $btn_delete = $('#btn-delete');
    var $btn_refresh = $('#btn-refresh');

    getAppInfo();

    function getAppInfo() {
        var url = "http://" + manager_host + "/app/info?app_id=" + application_id + "&config=true";
        $.ajax({
            dataType: "json",
            url: url,
            success: function(data) {
                if (data.result != "ok") {
                    showWarningToast("operation failed", data.message);
                } else {
                    document.getElementById("app-info-json").textContent = JSON.stringify(data.app_info, undefined, 4);
                    document.getElementById("app-config-json").textContent = JSON.stringify(data.app_config, undefined, 4);
                }

                hideWaitScreen();
            },
            error: function() {
                showWarningToast("error", "request service failed");
                hideWaitScreen();
            }
        });
    }
}