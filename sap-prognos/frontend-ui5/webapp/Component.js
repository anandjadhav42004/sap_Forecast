sap.ui.define([
    "sap/ui/core/UIComponent",
    "sap/ui/model/json/JSONModel"
], function (UIComponent, JSONModel) {
    "use strict";
    return UIComponent.extend("sap.prognos.Component", {
        metadata: {
            manifest: "json"
        },
        init: function () {
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
            var oSessionModel = new JSONModel(oSessionData);
            this.setModel(oSessionModel, "session");
            sap.ui.getCore().setModel(oSessionModel, "session");

            // call the init function of the parent
            UIComponent.prototype.init.apply(this, arguments);
            
            // initialize the router
            this.getRouter().initialize();
        }
    });
});
