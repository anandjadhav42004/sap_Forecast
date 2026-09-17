# SAP Prognos — Professor Demo & Viva Presentation Script

This guide gives you the exact script, talking points, and answers to crush your final year project presentation and viva.

---

## ⏱️ 1. The 60-Second Elevator Pitch

> *"Respected Professor/Panel, supply chain stockouts and excess inventory cost global retailers billions annually. Traditional ERP systems often rely on simple rolling averages that fail to anticipate seasonal shifts or promotions.*
>
> *Our project, **SAP Prognos**, is an **Enterprise AI Demand Forecasting and Inventory Optimization Platform**. We combined **XGBoost gradient boosting** with the **SAP Fiori Horizon Design System** and **FastAPI microservices**.*
>
> *Key achievements: We reduced demand forecasting error (MAPE) from **17.4% (Baseline)** down to **12.9% (XGBoost)**, integrated **Explainable AI (XAI)** to tell planners WHY demand is shifting, implemented **What-If simulation** for promotions, and automated replenishment recommendations across 99 monitored store-item pairs."*

---

## 🎬 2. The 5-Minute Live Demo Flow

### Step 1: Clean Startup & Architecture (30 Seconds)
- Run `./start_demo.sh` from the project directory.
- Explain: *"Our backend is an asynchronous FastAPI microservice with a loaded XGBoost booster and SQLite inventory store, and our frontend is an enterprise SAPUI5 single-page application."*

### Step 2: Role-Based Access Control (RBAC) (30 Seconds)
- Start on the login screen (`http://localhost:8080/webapp/index.html`).
- Log in first as **`user` / `user`**:
  - Show the sidebar: Only **Dashboard**, **Simulator**, and **Analytics** are visible. **Inventory** and **Settings** are protected and hidden.
  - Open the profile popover (`DU` avatar): Shows *"Demo User | Viewer (Read-Only)"*.
- Log out and log back in as **`admin` / `admin`**:
  - Show that **Inventory** and **Settings** immediately unlock with full operational controls.

### Step 3: Executive Dashboard & Explainable AI (90 Seconds)
- Point to the **KPI Strip**:
  - *50 Items Tracked*
  - *87.1% Avg Forecast Accuracy (12.9% MAPE)*
  - *99 Active Reorder Alerts*
- Point to the **Banner**: Shows predicted low stock requiring attention.
- Click **"Get Forecast"**:
  - Highlight the predicted demand value: **`33.6 units`** with 85% confidence interval bands.
  - Show the **Actual vs. Forecasted Chart**: Smooth curve with historical trend and forward projection.
  - **Crucial Talking Point (Explainable AI)**: *"Notice the AI Drivers panel. We don't just output a black-box number. The XGBoost tree-gain feature importance tells the planner that recent weekly demand is trending down (-62.1% impact) while weekday baseline contributes -4.2%."*

### Step 4: What-If Demand Simulator (45 Seconds)
- Navigate to **Simulator** in the sidebar.
- Adjust the **Demand Slider (+20%)**, enable **Promotion (+15%)**, enable **High Seasonality (+10%)**.
- Click **"Run Simulation"**:
  - Compare **Current Forecast (33.6 units)** vs **Simulated Forecast (51.01 units)**.
  - Show the automated recalculation: **Shortage: 19 units**, **Recommended Order: 86 units**.
  - Talking point: *"This allows planners to test promotional campaigns or holiday surges before placing purchase orders."*

### Step 5: Master Inventory & CSV Export (45 Seconds)
- Navigate to **Inventory** in the sidebar.
- Show the 99 items sorted by critical risk and days of cover.
- Type `"CRITICAL"` or `"Store 7"` in the search field to demonstrate live filtering.
- Click **"Export CSV"**: Demonstrates enterprise reporting by downloading `SAP_Prognos_Inventory_Reorder_Report.csv` directly to the browser.
- Click **"Trigger PO"** on the top critical item to demonstrate ERP PO generation.

### Step 6: Advanced Analytics & Anomaly Detection (30 Seconds)
- Navigate to **Analytics**.
- Show the benchmark progress bars:
  - Baseline (7-Day MA): `17.4%` (Error/Red)
  - Prophet: `17.0%` (Warning/Orange)
  - XGBoost: `12.9%` (Success/Green — Leader)
- Click **"Run Anomaly Scan"**: Shows statistical Z-score outlier detection identifying historical demand spikes.

### Step 7: System Settings & Live Telemetry (30 Seconds)
- Navigate to **Settings**.
- Show live telemetry: Microservice status `Online / Healthy`, Model loaded in memory (`XGBoost v1.0.0`), Database connected.
- Refresh the browser on `#/main`: Show that the admin session persists seamlessly without forcing re-login.

---

## ❓ 3. Top 10 Viva Questions & Expert Answers

#### Q1: Why did you choose XGBoost instead of Deep Learning (LSTM / Transformer)?
> **Answer**: *"For tabular multi-series retail demand data, tree-based gradient boosting consistently outperforms recurrent neural networks (as proven by the M5 Makridakis competition). XGBoost requires significantly less training time, has zero GPU dependency for inference (sub-20ms latency), handles missing values gracefully, and allows transparent feature-gain extraction for Explainable AI (XAI)."*

#### Q2: How did you engineer features for the time-series model?
> **Answer**: *"We avoided raw sequential dates to eliminate non-stationarity. Instead, we extracted: (1) Calendar cyclicality (day-of-week, month, weekend indicator), (2) Autoregressive lag features (`sales_lag_1` for daily momentum, `sales_lag_7` for weekly seasonality), and (3) Rolling window aggregations (`sales_roll_mean_7` for underlying trend)."*

#### Q3: How do you prevent data leakage during lag creation and training?
> **Answer**: *"All lag features are constructed strictly using backward-shifted historical values ($t-1$, $t-7$). In rolling statistics, we ensure the current target period $t$ is excluded. Model validation was conducted using chronological time-based splitting rather than random K-Fold shuffling."*

#### Q4: Why did you evaluate both Prophet and XGBoost?
> **Answer**: *"Facebook Prophet decomposes time-series into trend, seasonality, and holidays additively, making it great for macro-level univariate series. However, retail inventory requires global cross-learning across 500 store-item combinations. XGBoost learns shared interaction weights across all series simultaneously, achieving a lower MAPE (12.9% vs Prophet's 17.0%)."*

#### Q5: What is the financial impact of a 4.5% MAPE reduction?
> **Answer**: *"In supply chain research, each 1% reduction in demand forecasting error typically translates to a 1–2% reduction in excess holding inventory and up to 3% fewer lost-sale stockouts. Lowering MAPE from 17.4% to 12.9% represents millions in annual savings for an enterprise enterprise scale retailer."*

#### Q6: How does the What-If simulation engine calculate inventory impact?
> **Answer**: *"It calculates Projected Demand during Lead Time: $\text{LTD} = \text{Simulated Daily Forecast} \times \text{Lead Time Days}$. If available stock (Current + Incoming) is less than LTD, the shortage is flagged as high risk and recommended order is calculated as $\text{Target Stock} - \text{Available Stock}$."*

#### Q7: How does your Anomaly Detection model work?
> **Answer**: *"We apply two-tailed Z-score standardization ($Z = \frac{x - \mu}{\sigma}$) on historical series. Any observation exceeding $|Z| > 2.0$ (~95% confidence threshold) is flagged as an anomaly (spike or dip), preventing corrupted data from skewing future lag averages."*

#### Q8: How would this deploy in a production SAP enterprise environment?
> **Answer**: *"Following the SAP BTP Clean Core methodology: The FastAPI predictive engine is containerized via Docker and deployed on **SAP AI Core** orchestrated by Argo Workflows. The business application layer runs on **SAP Cloud Application Programming Model (SAP CAP)**, persisting master inventory in **SAP HANA Cloud** and authenticating via BTP XSUAA."*

#### Q9: How is Role-Based Access Control (RBAC) handled in the frontend?
> **Answer**: *"The SAPUI5 application binds navigation items to a global `session` JSONModel. Navigation list items and administrative action buttons use expression binding: `visible='{= ${session>/role} === &quot;admin&quot; }'`. When a viewer logs in, administrative tabs (Inventory, Settings, PO triggers) are completely removed from the DOM and router."*

#### Q10: What are the primary limitations and next steps for this project?
> **Answer**: *"Current limitations include running on a prototype SQLite database rather than live SAP S/4HANA OData federation. Future scope involves evaluating zero-shot foundation models (e.g., Amazon Chronos or Google TimesFM) and implementing hierarchical coherent reconciliation across regional warehouses."*
