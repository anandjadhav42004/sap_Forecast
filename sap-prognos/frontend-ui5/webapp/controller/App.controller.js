sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel"
], function (Controller, JSONModel) {
    "use strict";
    return Controller.extend("sap.prognos.controller.App", {
        onInit: function () {
            // Apply Horizon Dark theme class to the body if needed
            document.body.classList.add("sapTheme-sap_horizon_dark");
            
            // Restore session from localStorage if available
            var sSavedSession = localStorage.getItem("sap_prognos_session");
            var oSessionData = { role: "guest", username: "" };
            if (sSavedSession) {
                try {
                    oSessionData = JSON.parse(sSavedSession);
                } catch (e) {
                    localStorage.removeItem("sap_prognos_session");
                }
            }
            var oCore = sap.ui.getCore();
            var oSessionModel = oCore.getModel("session");
            if (!oSessionModel) {
                oSessionModel = new JSONModel(oSessionData);
                oCore.setModel(oSessionModel, "session");
            } else {
                oSessionModel.setData(oSessionData);
            }
            if (this.getOwnerComponent()) {
                this.getOwnerComponent().setModel(oSessionModel, "session");
            }
            this.getView().setModel(oSessionModel, "session");
        }
    });
});
