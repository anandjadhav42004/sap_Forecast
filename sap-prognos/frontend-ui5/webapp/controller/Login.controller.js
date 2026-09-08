sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageToast"
], function (Controller, JSONModel, MessageToast) {
    "use strict";

    return Controller.extend("sap.prognos.controller.Login", {
        onInit: function () {
            var oModel = new JSONModel({
                username: "",
                password: ""
            });
            this.getView().setModel(oModel);
            
            // Set up a global model for session/role if not exists
            var oCore = sap.ui.getCore();
            if (!oCore.getModel("session")) {
                oCore.setModel(new JSONModel({ role: "guest", username: "" }), "session");
            }
        },
        
        onLogin: function () {
            var oModel = this.getView().getModel();
            var sUser = oModel.getProperty("/username");
            var sPass = oModel.getProperty("/password");
            
            if (!sUser || !sPass) {
                MessageToast.show("Please enter both username and password.");
                return;
            }
            
            var sRole = "";
            if (sUser.toLowerCase() === "admin" && sPass === "admin") {
                sRole = "admin";
            } else if (sUser.toLowerCase() === "user" && sPass === "user") {
                sRole = "user";
            } else {
                MessageToast.show("Invalid credentials. Try admin/admin or user/user.");
                return;
            }
            
            // Set global session
            sap.ui.getCore().getModel("session").setData({
                role: sRole,
                username: sUser
            });
            
            MessageToast.show("Welcome, " + sUser + "!");
            
            // Clear inputs
            oModel.setProperty("/username", "");
            oModel.setProperty("/password", "");
            
            // Navigate to main dashboard
            var oRouter = this.getOwnerComponent().getRouter();
            oRouter.navTo("main");
        }
    });
});
