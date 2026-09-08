sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/m/MessageToast"
], function (Controller, JSONModel, MessageToast) {
    "use strict";

    return Controller.extend("sap.prognos.controller.Main", {
        onInit: function () {
            var oData = {
                store: 2,
                item: 10,
                date: "2018-01-01",
                salesLag1: 41.0,
                salesLag7: 45.0,
                salesRollMean7: 41.7,
                forecastResult: "---",
                isBusy: false,
                reorderAlertsCount: 0,
                reorderAlerts: [],
                explainability: [],
                simStore: 2,
                simItem: 10,
                simDemandAdjust: 20,
                simPromotion: true,
                simSeasonality: true,
                simCurrentForecast: "---",
                simSimulatedForecast: "---",
                simInventoryImpact: 0,
                simRecommendedOrder: 0
            };
            var oModel = new JSONModel(oData);
            this.getView().setModel(oModel);
            
            // Bind the global session model to this view
            var oSessionModel = sap.ui.getCore().getModel("session");
            if (oSessionModel) {
                this.getView().setModel(oSessionModel, "session");
            }
            
            this._loadMetrics();
            this._loadReorderAlerts();
        },
        
        _getApiBaseUrl: function () {
            // Use local backend for localhost dev, otherwise use Render production URL
            if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
                return "http://localhost:8000";
            }
            return "https://sap-forecast.onrender.com";
        },
        
        _loadMetrics: function () {
            var oModel = this.getView().getModel();
            fetch(this._getApiBaseUrl() + "/metrics")
                .then(response => response.json())
                .then(data => {
                    var xgboostMape = data.metrics["XGBoost (Full Global)"].MAPE.toFixed(1);
                    var prophetMape = data.metrics["Prophet (Sampled)"].MAPE.toFixed(1);
                    var baselineMape = data.metrics["Baseline (7-Day MA)"].MAPE.toFixed(1);
                    
                    oModel.setProperty("/accuracyMape", xgboostMape + "%");
                    oModel.setProperty("/accuracyAccuracy", (100 - parseFloat(xgboostMape)).toFixed(1) + "%");
                    oModel.setProperty("/prophetMape", prophetMape + "%");
                    oModel.setProperty("/baselineMape", baselineMape + "%");
                })
                .catch(err => {
                    console.error("Failed to fetch metrics", err);
                    oModel.setProperty("/accuracyAccuracy", "---%");
                });
        },
        
        _loadReorderAlerts: function () {
            var oModel = this.getView().getModel();
            fetch(this._getApiBaseUrl() + "/reorder-alerts")
                .then(response => response.json())
                .then(data => {
                    oModel.setProperty("/reorderAlertsCount", data.count);
                    var alerts = data.alerts.slice(0, 10).map(function(alert) {
                        var isCritical = alert.current_stock < (alert.safety_stock * 0.5);
                        return {
                            store: alert.store,
                            item: alert.item,
                            currentStock: alert.current_stock,
                            safetyStock: alert.safety_stock,
                            statusText: isCritical ? "Critical" : "Low",
                            trendIcon: isCritical ? "sap-icon://error" : "sap-icon://warning2",
                            trendColor: isCritical ? "Error" : "Critical"
                        };
                    });
                    oModel.setProperty("/reorderAlerts", alerts);
                })
                .catch(err => console.error("Failed to fetch reorder alerts", err));
        },
        
        onAfterRendering: function () {
            // Wait slightly for DOM to settle
            setTimeout(this._setupChart.bind(this), 200);
        },
        
        _setupChart: function (forecastVal, confLower, confUpper) {
            var canvas = document.getElementById("forecastChart");
            if (!canvas) return;
            var ctx = canvas.getContext('2d');
            
            // Destroy existing chart instance if it exists
            if (this._chartInstance) {
                this._chartInstance.destroy();
            }
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            var historyData = [45, 38, 42, 40, 47, 39, 41];
            var labels = ["Day -6", "Day -5", "Day -4", "Day -3", "Day -2", "Day -1", "Today", "Forecast"];
            
            // Only pad history with null for forecast point if we are actually drawing the forecast
            var historyDataset = forecastVal ? [...historyData, null] : historyData;
            
            var datasets = [
                {
                    label: 'Historical Sales',
                    data: historyDataset,
                    borderColor: '#38bdf8', // Cyan
                    backgroundColor: '#38bdf8',
                    borderWidth: 3,
                    tension: 0.4, // Smoother curve
                    pointRadius: 5,
                    pointBackgroundColor: '#0f172a',
                    pointBorderColor: '#38bdf8',
                    pointBorderWidth: 2,
                    shadowBlur: 10,
                    shadowColor: 'rgba(56, 189, 248, 0.8)'
                }
            ];
            
            if (forecastVal) {
                var lastHistorical = historyData[historyData.length - 1];
                // Forecast line connecting last point to forecast
                var forecastDataset = [null, null, null, null, null, null, lastHistorical, forecastVal];
                
                // Confidence bounds (start from last historical point)
                var upperBound = [null, null, null, null, null, null, lastHistorical, confUpper || (forecastVal * 1.1)];
                var lowerBound = [null, null, null, null, null, null, lastHistorical, confLower || (forecastVal * 0.9)];
                
                datasets.push({
                    label: 'Upper Bound',
                    data: upperBound,
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    pointRadius: 0,
                    fill: false
                });
                
                datasets.push({
                    label: 'Confidence Band',
                    data: lowerBound,
                    borderColor: 'transparent',
                    backgroundColor: 'rgba(217, 70, 239, 0.15)', // Magenta shade
                    pointRadius: 0,
                    fill: 1 // Absolute index of Upper Bound dataset (which is index 1)
                });
                
                datasets.push({
                    label: 'Forecast',
                    data: forecastDataset,
                    borderColor: '#d946ef', // Magenta
                    backgroundColor: '#d946ef',
                    borderWidth: 3,
                    borderDash: [6, 6],
                    tension: 0.4,
                    pointRadius: [0,0,0,0,0,0,0,6],
                    pointBackgroundColor: '#0f172a',
                    pointBorderColor: '#d946ef',
                    pointBorderWidth: 2,
                    shadowBlur: 10,
                    shadowColor: 'rgba(217, 70, 239, 0.8)'
                });
            }
            
            this._chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
                        }
                    }
                }
            });
        },

        onGetForecast: function () {
            var oView = this.getView();
            var oModel = oView.getModel();
            
            var store = parseInt(oModel.getProperty("/store"));
            var item = parseInt(oModel.getProperty("/item"));
            var date = oModel.getProperty("/date");
            
            if (!store || !item || !date) {
                MessageToast.show("Please fill all input fields.");
                return;
            }

            oModel.setProperty("/isBusy", true);
            oModel.setProperty("/forecastResult", "...");

            var payload = {
                store: store,
                item: item,
                date: date,
                sales_lag_1: parseFloat(oModel.getProperty("/salesLag1")) || 0,
                sales_lag_7: parseFloat(oModel.getProperty("/salesLag7")) || 0,
                sales_roll_mean_7: parseFloat(oModel.getProperty("/salesRollMean7")) || 0
            };
            
            // Wait a bit to simulate network delay so the busy indicator is visible
            setTimeout(function() {
                fetch(this._getApiBaseUrl() + "/forecast", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.json();
                })
                .then(data => {
                    oModel.setProperty("/isBusy", false);
                    
                    // Parse float and fix to 1 decimal place
                    var formattedResult = parseFloat(data.forecasted_sales).toFixed(1) + " units";
                    oModel.setProperty("/forecastResult", formattedResult);
                    oModel.setProperty("/explainability", data.explainability);
                    this._setupChart(data.forecasted_sales, data.confidence_lower, data.confidence_upper);
                    oModel.setProperty("/lastUpdated", new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
                    this.byId("lastUpdatedKpi").setText(oModel.getProperty("/lastUpdated"));
                    
                    // Update Chart
                    // already called above
                    
                    MessageToast.show("Forecast generated successfully.");
                })
                .catch(error => {
                    oModel.setProperty("/isBusy", false);
                    oModel.setProperty("/forecastResult", "Error");
                    MessageToast.show("API server unreachable. Ensure backend is running.", { duration: 5000 });
                    console.error(error);
                });
            }.bind(this), 300);
        },

        
        onRunSimulation: function () {
            var oModel = this.getView().getModel();
            oModel.setProperty("/isBusy", true);
            
            var payload = {
                store: parseInt(oModel.getProperty("/simStore")),
                item: parseInt(oModel.getProperty("/simItem")),
                date: "2018-01-01",
                sales_lag_1: 41.0,
                sales_lag_7: 45.0,
                sales_roll_mean_7: 41.7,
                demand_adjustment_pct: parseFloat(oModel.getProperty("/simDemandAdjust")),
                is_promotion: oModel.getProperty("/simPromotion"),
                high_seasonality: oModel.getProperty("/simSeasonality")
            };
            
            fetch(this._getApiBaseUrl() + "/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                oModel.setProperty("/isBusy", false);
                oModel.setProperty("/simCurrentForecast", data.current_forecast + " units");
                oModel.setProperty("/simSimulatedForecast", data.simulated_forecast + " units");
                oModel.setProperty("/simInventoryImpact", data.inventory_impact_units);
                oModel.setProperty("/simRecommendedOrder", data.recommended_order);
                MessageToast.show("Simulation complete.");
            })
            .catch(error => {
                oModel.setProperty("/isBusy", false);
                MessageToast.show("Simulation failed.");
            });
        },

        onSideNavSelect: function (oEvent) {
            var sKey = oEvent.getParameter("item").getKey();
            this.byId("pageContainer").to(this.byId(sKey));
        },

        onCollapseExpandPress: function () {
            var oSideNavigation = this.byId("sideNavigation");
            var bExpanded = oSideNavigation.getExpanded();
            oSideNavigation.setExpanded(!bExpanded);
        },
        
        onInventorySearch: function (oEvent) {
            var sQuery = oEvent.getParameter("newValue");
            var oTable = this.byId("inventoryTable");
            var oBinding = oTable.getBinding("items");
            var aFilters = [];
            
            if (sQuery && sQuery.length > 0) {
                var filterStore = new sap.ui.model.Filter("store", sap.ui.model.FilterOperator.EQ, parseInt(sQuery) || -1);
                var filterItem = new sap.ui.model.Filter("item", sap.ui.model.FilterOperator.EQ, parseInt(sQuery) || -1);
                var filterRisk = new sap.ui.model.Filter("risk", sap.ui.model.FilterOperator.Contains, sQuery.toUpperCase());
                
                aFilters.push(new sap.ui.model.Filter({
                    filters: [filterStore, filterItem, filterRisk],
                    and: false
                }));
            }
            oBinding.filter(aFilters);
        },
        
        onRunAnomalies: function () {
            var oModel = this.getView().getModel();
            oModel.setProperty("/isBusyAnomalies", true);
            
            // Mocking historical payload
            var payload = {
                store: 2,
                item: 10,
                historical_sales: [
                    {date: "2017-12-01", sales: 40},
                    {date: "2017-12-02", sales: 42},
                    {date: "2017-12-03", sales: 45},
                    {date: "2017-12-04", sales: 41},
                    {date: "2017-12-05", sales: 38},
                    {date: "2017-12-06", sales: 120}, // Spike anomaly
                    {date: "2017-12-07", sales: 44},
                    {date: "2017-12-08", sales: 10}  // Dip anomaly
                ]
            };
            
            fetch(this._getApiBaseUrl() + "/anomalies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                oModel.setProperty("/isBusyAnomalies", false);
                oModel.setProperty("/anomalies", data.anomalies);
                oModel.setProperty("/anomaliesCount", data.anomalies_detected);
                MessageToast.show("Anomaly scan complete.");
            })
            .catch(error => {
                oModel.setProperty("/isBusyAnomalies", false);
                MessageToast.show("Failed to run anomaly scan.");
            });
        }
    });
});
