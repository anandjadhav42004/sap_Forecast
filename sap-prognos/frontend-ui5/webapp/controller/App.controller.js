sap.ui.define([
    "sap/ui/core/mvc/Controller"
], function (Controller) {
    "use strict";
    return Controller.extend("sap.prognos.controller.App", {
        onInit: function () {
            // Apply Horizon Dark theme class to the body if needed, 
            // though index.html bootstrap is better
            document.body.classList.add("sapTheme-sap_horizon_dark");
        }
    });
});
