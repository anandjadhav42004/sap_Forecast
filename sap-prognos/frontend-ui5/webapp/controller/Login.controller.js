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
            
            // Check localStorage for saved session
            var sSavedSession = localStorage.getItem("sap_prognos_session");
            var oSessionData = { role: "guest", username: "" };
            if (sSavedSession) {
                try {
                    oSessionData = JSON.parse(sSavedSession);
                } catch (e) {
                    localStorage.removeItem("sap_prognos_session");
                }
            }
            
            // Set up a global model for session/role
            var oCore = sap.ui.getCore();
            if (!oCore.getModel("session")) {
                oCore.setModel(new JSONModel(oSessionData), "session");
            } else {
                oCore.getModel("session").setData(oSessionData);
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
            var sFullName = "";
            var sRoleName = "";
            var sEmail = "";
            var sAvatarText = "";
            if (sUser.toLowerCase() === "admin" && sPass === "admin") {
                sRole = "admin";
                sFullName = "Anand Jadhav";
                sRoleName = "Administrator";
                sEmail = "anand.jadhav@sap-prognos.internal";
                sAvatarText = "AJ";
            } else if (sUser.toLowerCase() === "user" && sPass === "user") {
                sRole = "user";
                sFullName = "Demo User";
                sRoleName = "Viewer (Read-Only)";
                sEmail = "demo.viewer@sap-prognos.internal";
                sAvatarText = "DU";
            } else {
                MessageToast.show("Invalid credentials. Try admin/admin or user/user.");
                return;
            }
            
            var sessionData = {
                role: sRole,
                username: sUser,
                fullName: sFullName,
                roleName: sRoleName,
                email: sEmail,
                avatarText: sAvatarText
            };
            
            // Save to localStorage for refresh persistence
            localStorage.setItem("sap_prognos_session", JSON.stringify(sessionData));
            
            // Set global and component session
            if (sap.ui.getCore().getModel("session")) {
                sap.ui.getCore().getModel("session").setData(sessionData);
            }
            if (this.getOwnerComponent() && this.getOwnerComponent().getModel("session")) {
                this.getOwnerComponent().getModel("session").setData(sessionData);
            }
            
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
