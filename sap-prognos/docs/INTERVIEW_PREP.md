# Interview Preparation & Comprehensive Defense Guide — SAP Prognos

This document prepares you for technical interviews, viva voce, and final-year project defense panels evaluating **SAP Prognos**.

---

## 1. High-Level System Architecture & SAP Ecosystem

### Q1: Can you explain the end-to-end architecture of SAP Prognos?
> **Answer:** 
> SAP Prognos is structured around a decoupled microservice architecture:
> 1. **Presentation Tier**: A Single Page Application (SPA) built with **SAPUI5** adhering to **SAP Fiori Horizon** guidelines, providing real-time KPI tiles, What-If simulation controls, and Chart.js analytical dashboards.
> 2. **Application & API Tier**: A high-performance asynchronous **FastAPI** Python microservice utilizing **Pydantic v2** for contract schema validation, orchestrating predictive inference, inventory mathematical models, and feature explainability.
> 3. **Machine Learning Tier**: A pre-trained **XGBoost** model paired with feature engineering pipelines (lags and rolling statistics) and **Prophet** baseline decompositions.
> 4. **Persistence Tier**: An inventory relational database (SQLite for local rapid prototyping, architected for migration to **SAP HANA Cloud**).

---

### Q2: How does this prototype translate to a production enterprise deployment on SAP BTP?
> **Answer:**
> In enterprise production, SAP Prognos adheres to SAP's **Clean Core** strategy on the **SAP Business Technology Platform (SAP BTP)**:
> - **SAP CAP (Cloud Application Programming Model)**: Serves as the enterprise extension and orchestration layer, exposing secure OData v4 / REST endpoints and managing multi-tenant business context.
> - **SAP HANA Cloud**: Replaces SQLite to store transactional inventory states, stock movements, and master data in-memory.
> - **SAP AI Core & SAP AI Launchpad**: The FastAPI + XGBoost runtime is packaged as a standard OCI/Docker container, registered in an enterprise registry, and executed in scalable Kubernetes environments managed by SAP AI Core via Argo Workflows.
> - **Security**: Enterprise identity federation via BTP **XSUAA / SAP Cloud Identity Services** with JWT OAuth2 tokens.

---

### Q3: Why didn't you use in-database Machine Learning via SAP HANA PAL or APL instead of a separate Python service on SAP AI Core?
> **Answer (Crucial for SAP examiners!):**
> "While SAP HANA PAL (Predictive Analysis Library) and APL (Automated Predictive Library) via `hana_ml` are excellent for in-database algorithms, deploying on **SAP AI Core** was selected for three clear architectural reasons:
> 1. **Hybrid Multi-Model Flexibility**: We required custom Python feature pipelines combining XGBoost with Prophet additive decompositions and custom lag generation that are difficult to express in pure SQLScript procedures.
> 2. **Real-time Explainability**: We extract real-time feature importance (tree split Gain) and SHAP values dynamically to drive our 'AI Drivers' explainability UI.
> 3. **Decoupled Compute Elasticity**: Offloading heavy ML batch retraining and iterative What-If simulations to containerized Kubernetes pods in SAP AI Core protects the primary transactional SAP HANA database from CPU/memory bottlenecks."

---

## 2. Machine Learning & Time Series Science

### Q4: Why did you choose XGBoost for time series forecasting over Deep Learning (LSTMs/Transformers) or classical ARIMA?
> **Answer:**
> 1. **Empirical Evidence from the M5 Competition**: The seminal Makridakis M5 Walmart forecasting competition (over 42,000 series) conclusively proved that Gradient Boosted Decision Trees (GBDTs like LightGBM and XGBoost) consistently outperform deep neural networks and ARIMA on structured retail sales data.
> 2. **Global Cross-Series Learning**: Unlike ARIMA, which must be fit to a single univariate series, XGBoost trains a single global model across all SKUs, learning shared seasonal and autoregressive patterns (demonstrated by our Full Global XGBoost achieving **12.93% MAPE**).
> 3. **Computational Efficiency & Latency**: XGBoost trains in seconds compared to hours for LSTMs and delivers sub-50ms inference latency required for our interactive What-If simulator.
> 4. **Transparency & Explainability**: XGBoost allows direct extraction of split gains, enabling us to explain predictions to business users without the opacity of deep neural nets.

---

### Q5: What is the role of Prophet in your project, and why use it if Meta has put Prophet in maintenance mode?
> **Answer:**
> - **Role in SAP Prognos**: Prophet is utilized as an **interpretable additive decomposition baseline**. It decomposes time series into clear trend, weekly/yearly Fourier seasonality, and holiday components ($\hat{y}(t) = g(t) + s(t) + h(t)$), which gives supply chain managers visual clarity into calendar drivers.
> - **Maintenance Mode Defense**: We are fully aware that Meta's Prophet (package `prophet`, superseding `fbprophet`) is in maintenance mode. We do not position Prophet as the state-of-the-art accuracy leader—our empirical results prove XGBoost achieves lower error (12.93% vs 16.99% MAPE). Instead, Prophet provides a transparent, interpretable benchmark. In our future scope, we identify modern active successors such as **NeuralProphet** and **Nixtla StatsForecast**.

---

### Q6: How are you handling the transition beyond the M4 competition in your academic literature review?
> **Answer:**
> "The M4 competition (2018) highlighted hybrid ML-statistical approaches. However, our literature review extends through:
> 1. **The M5 Competition (2020)**: Focused on retail demand and proved GBDT dominance in hierarchical sales forecasting, which directly grounds our XGBoost architecture.
> 2. **The Monash Time Series Archive (NeurIPS 2021)**: The standard academic benchmark repository for global time series models.
> 3. **Time Series Foundation Models (2023–2026)**: We acknowledge the emerging paradigm of zero-shot pre-trained foundation models like **Amazon Chronos (ICML 2024)**, **Google TimesFM (ICML 2024)**, and **Nixtla TimeGPT-1**, positioning them as exciting candidates for future SAP AI Core Generative AI Hub integration."

---

### Q7: How does your Explainable AI (XAI) feature work?
> **Answer:**
> Rather than treating the ML model as a black box, the FastAPI backend queries the XGBoost booster's internal graph using:
> ```python
> booster.get_score(importance_type="gain")
> ```
> Gain measures the average improvement in accuracy brought by a feature across all tree splits where it appears. We map these numeric weights into human-readable business drivers (e.g., 'Recent 7-day momentum', 'Day-of-week seasonality', 'Prior day baseline') so procurement planners understand *why* the forecast shifted.

---

## 3. Supply Chain & Inventory Optimization Logic

### Q8: How does the system translate raw forecasts into inventory recommendations?
> **Answer:**
> Forecasting alone does not solve supply chain problems; decisions must account for lead times. Our backend calculates:
> 1. **Expected Lead-Time Demand (LTD)**: $\text{Daily Forecast} \times \text{Supplier Lead Time (Days)}$.
> 2. **Shortage Risk Classification**: If $(\text{Current Stock} + \text{Incoming Stock}) < \text{LTD}$, the item is flagged as **HIGH/CRITICAL RISK** because stock will run out before supplier replenishment arrives.
> 3. **Recommended Order Quantity**: 
>    $$Q_{\text{reorder}} = \max(0, \text{Target Stock} - (\text{Current Stock} + \text{Incoming Stock}))$$
> This guarantees inventory levels return to safe buffer targets while minimizing excess working capital.

---

### Q9: How does the What-If Simulation work under the hood?
> **Answer:**
> When a user adjusts percentage sliders, promotion toggles, or seasonality multipliers on the SAPUI5 interface:
> 1. The client dispatches a POST request with the scenario delta vector to `/simulate`.
> 2. The backend generates base ML predictions and applies the scenario multipliers across the forward horizon.
> 3. The inventory optimization service immediately recalculates projected daily stock burn, stockout dates, and modified reorder quantities.
> 4. The response updates Chart.js line charts and status badges in real time, allowing planners to stress-test their supply chain before committing purchase orders.

---

## 4. Frontend & Security

### Q10: Why did you build the UI in SAPUI5 rather than standard React or Angular?
> **Answer:**
> In enterprise environments running SAP S/4HANA or SAP BTP, business users expect consistency with the **SAP Fiori User Experience (UX)**. SAPUI5 provides enterprise-grade data binding (OData and JSONModel), built-in accessibility, responsive layout grids, and strict adherence to the **SAP Fiori Horizon** design standard, making adoption seamless for enterprise supply chain operators.

### Q11: How is Role-Based Access Control (RBAC) enforced?
> **Answer:**
> The UI leverages SAPUI5's two-way data binding and expression binding against a session `JSONModel`. Depending on whether the logged-in profile is `admin`, `planner`, or `viewer`, sensitive operational controls (such as editing target stock, manual reorder overrides, and system settings) are conditionally rendered or disabled via expressions like:
> ```xml
> visible="{= ${session>/role} === 'admin' }"
> ```
