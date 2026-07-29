// Auto-dismiss des alertes après quelques secondes
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        document.querySelectorAll(".alert").forEach(function (alert) {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);
});
