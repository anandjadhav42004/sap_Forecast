sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageToast"
], function (Controller, JSONModel, MessageToast) {
    "use strict";

    return Controller.extend("sap.prognos.controller.Login", {

        onInit: function () {
            var oModel = new JSONModel({
                username: "",  password: "",
                username2: "", password2: ""
            });
            this.getView().setModel(oModel);

            // Restore saved session if exists
            var sSaved = localStorage.getItem("sap_prognos_session");
            var oSession = { role: "guest", username: "" };
            if (sSaved) {
                try { oSession = JSON.parse(sSaved); } catch (e) {
                    localStorage.removeItem("sap_prognos_session");
                }
            }

            var oCore = sap.ui.getCore();
            if (!oCore.getModel("session")) {
                oCore.setModel(new JSONModel(oSession), "session");
            } else {
                oCore.getModel("session").setData(oSession);
            }
        },

        // ── Admin Login ──────────────────────────────────────────
        onLogin: function () {
            var oModel = this.getView().getModel();
            var sUser  = (oModel.getProperty("/username")  || "").trim();
            var sPass  = (oModel.getProperty("/password")  || "");

            if (!sUser || !sPass) {
                MessageToast.show("Username aur password dono daalo.");
                return;
            }
            if (sUser.toLowerCase() !== "admin" || sPass !== "admin") {
                MessageToast.show("Invalid Admin credentials. Use admin / admin");
                return;
            }
            this._doLogin({
                role:       "admin",
                username:   "admin",
                fullName:   "Anand Jadhav",
                roleName:   "Administrator",
                email:      "anand.jadhav@sap-prognos.internal",
                avatarText: "AJ"
            });
        },

        // ── User / Viewer Login ──────────────────────────────────
        onLoginUser: function () {
            var oModel = this.getView().getModel();
            var sUser  = (oModel.getProperty("/username2") || "").trim();
            var sPass  = (oModel.getProperty("/password2") || "");

            if (!sUser || !sPass) {
                MessageToast.show("Username aur password dono daalo.");
                return;
            }
            if (sUser.toLowerCase() !== "user" || sPass !== "user") {
                MessageToast.show("Invalid Viewer credentials. Use user / user");
                return;
            }
            this._doLogin({
                role:       "user",
                username:   "user",
                fullName:   "Demo Viewer",
                roleName:   "Viewer (Read-Only)",
                email:      "viewer@sap-prognos.internal",
                avatarText: "DV"
            });
        },

        // ── Shared session setup & navigate ─────────────────────
        _doLogin: function (oData) {
            localStorage.setItem("sap_prognos_session", JSON.stringify(oData));

            var oCore = sap.ui.getCore();
            if (oCore.getModel("session")) {
                oCore.getModel("session").setData(oData);
            }
            if (this.getOwnerComponent() && this.getOwnerComponent().getModel("session")) {
                this.getOwnerComponent().getModel("session").setData(oData);
            }

            MessageToast.show("Welcome, " + oData.fullName + "! 🚀");

            // Clear inputs
            var oModel = this.getView().getModel();
            oModel.setData({ username: "", password: "", username2: "", password2: "" });

            this.getOwnerComponent().getRouter().navTo("main");
        }
    });
});
