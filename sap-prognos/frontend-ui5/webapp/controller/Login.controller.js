sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageToast"
], function (Controller, JSONModel, MessageToast) {
    "use strict";

    return Controller.extend("sap.prognos.controller.Login", {

        onInit: function () {
            var oModel = new JSONModel({
                username: "admin",
                password: "admin",
                selectedRole: "admin",
                credHintText: "Default Admin: admin / admin",
                isPasswordMasked: true,
                isAuthenticating: false,
                hasError: false,
                errorMessage: ""
            });
            this.getView().setModel(oModel);
        },

        _getApiBaseUrl: function () {
            if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
                return "http://localhost:8000";
            }
            return "https://sap-forecast.onrender.com";
        },

        onRoleChange: function (oEvent) {
            var sKey = oEvent.getParameter("item").getKey();
            var oModel = this.getView().getModel();
            oModel.setProperty("/selectedRole", sKey);
            oModel.setProperty("/hasError", false);
            oModel.setProperty("/errorMessage", "");

            if (sKey === "admin") {
                oModel.setProperty("/username", "admin");
                oModel.setProperty("/password", "admin");
                oModel.setProperty("/credHintText", "Default Admin: admin / admin");
            } else {
                oModel.setProperty("/username", "user");
                oModel.setProperty("/password", "user");
                oModel.setProperty("/credHintText", "Default Viewer: user / user");
            }
        },

        onFillCredentials: function () {
            var oModel = this.getView().getModel();
            var sRole = oModel.getProperty("/selectedRole");
            if (sRole === "admin") {
                oModel.setProperty("/username", "admin");
                oModel.setProperty("/password", "admin");
            } else {
                oModel.setProperty("/username", "user");
                oModel.setProperty("/password", "user");
            }
            oModel.setProperty("/hasError", false);
            MessageToast.show("Credentials loaded for " + (sRole === "admin" ? "Administrator" : "Viewer"));
        },

        onTogglePassword: function () {
            var oModel = this.getView().getModel();
            var bMasked = oModel.getProperty("/isPasswordMasked");
            oModel.setProperty("/isPasswordMasked", !bMasked);
        },

        onLogin: function () {
            var oModel = this.getView().getModel();
            var sUser = (oModel.getProperty("/username") || "").trim();
            var sPass = (oModel.getProperty("/password") || "");

            if (!sUser || !sPass) {
                oModel.setProperty("/hasError", true);
                oModel.setProperty("/errorMessage", "Please enter both username and password.");
                return;
            }

            oModel.setProperty("/isAuthenticating", true);
            oModel.setProperty("/hasError", false);
            oModel.setProperty("/errorMessage", "");

            var that = this;
            fetch(this._getApiBaseUrl() + "/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: sUser, password: sPass })
            })
            .then(function (res) {
                if (!res.ok) {
                    return res.json().then(function (data) {
                        throw new Error(data.detail || "Authentication failed. Invalid username or password.");
                    });
                }
                return res.json();
            })
            .then(function (data) {
                oModel.setProperty("/isAuthenticating", false);
                that._establishSessionAndNavigate(data);
            })
            .catch(function (err) {
                oModel.setProperty("/isAuthenticating", false);
                // Check if backend unreachable vs wrong credentials
                if (err.message && err.message.indexOf("Failed to fetch") !== -1) {
                    // Fallback for demo when backend is starting or offline
                    if (sUser === "admin" && sPass === "admin") {
                        that._establishSessionAndNavigate({
                            role: "admin", username: "admin", fullName: "Anand Jadhav",
                            roleName: "Administrator", email: "anand.jadhav@sap-prognos.internal",
                            avatarText: "AJ", token: "demo-admin-bearer-token"
                        });
                        return;
                    } else if (sUser === "user" && sPass === "user") {
                        that._establishSessionAndNavigate({
                            role: "user", username: "user", fullName: "Demo User",
                            roleName: "Viewer (Read-Only)", email: "demo.viewer@sap-prognos.internal",
                            avatarText: "DU", token: "demo-user-bearer-token"
                        });
                        return;
                    }
                    oModel.setProperty("/hasError", true);
                    oModel.setProperty("/errorMessage", "Backend server unreachable. Please verify FastAPI is running on port 8000.");
                } else {
                    oModel.setProperty("/hasError", true);
                    oModel.setProperty("/errorMessage", err.message || "Invalid credentials. Use admin/admin or user/user.");
                }
            });
        },

        _establishSessionAndNavigate: function (oSessionData) {
            localStorage.setItem("sap_prognos_session", JSON.stringify(oSessionData));

            var oCore = sap.ui.getCore();
            if (oCore.getModel("session")) {
                oCore.getModel("session").setData(oSessionData);
            } else {
                oCore.setModel(new JSONModel(oSessionData), "session");
            }
            if (this.getOwnerComponent() && this.getOwnerComponent().getModel("session")) {
                this.getOwnerComponent().getModel("session").setData(oSessionData);
            }

            MessageToast.show("Authenticated as " + oSessionData.fullName + " (" + oSessionData.roleName + ") 🚀");

            var oRouter = this.getOwnerComponent() ? this.getOwnerComponent().getRouter() : null;
            if (oRouter) {
                oRouter.navTo("main");
            } else {
                window.location.hash = "#/main";
                window.location.reload();
            }
        }
    });
});
