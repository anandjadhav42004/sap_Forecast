# Interview Preparation & System Defense - SAP Prognos

This document is designed to help you defend SAP Prognos during technical interviews or final-year project evaluations.

## 1. System Architecture
**Q: How is the application structured?**
**A:** It's a decoupled architecture. The frontend is a Single Page Application (SPA) built with SAPUI5, deployed on Vercel. The backend is a FastAPI (Python) microservice deployed on Render. They communicate via RESTful APIs over HTTPS.

## 2. Machine Learning
**Q: Why XGBoost over Deep Learning (LSTMs) or ARIMA?**
**A:** ARIMA struggles with complex non-linear features (like promotions and weekends). LSTMs require massive datasets and are a "black box" that is hard to explain to supply chain managers. XGBoost handles tabular data exceptionally well, is computationally fast for real-time APIs, and allows us to extract feature importance (Gain) to build our "AI Drivers" explainability feature.

**Q: How did you implement Explainable AI (XAI)?**
**A:** Instead of showing the user a raw number, the FastAPI backend intercepts the XGBoost model's internal tree structure using `get_booster().get_score(importance_type='gain')`. We map these gains to the specific lag and seasonality features to tell the user *why* demand is going up or down.

## 3. Inventory Mathematics
**Q: How do you calculate Reorder Recommendations?**
**A:** We use standard supply chain logic. We calculate the expected demand during the lead time (`Forecast * Lead Time`). If the `Current Stock + Incoming Stock` is less than this expected demand, a reorder is triggered. The recommended order quantity brings the stock back up to the predefined `Target Stock`.

## 4. Frontend & Security
**Q: How does the Role-Based UI work?**
**A:** We use SAPUI5 Routing and a global JSONModel (`session`). When a user logs in, their role is set in the model. Components like the Inventory and Settings tabs use expression binding (`visible="{= ${session>/role} === 'admin' }"`) to dynamically hide themselves if the user lacks permissions.

**Q: Is the system secure?**
**A:** We enforce CORS policies on the backend to only accept requests from the Vercel frontend. The APIs use strict Pydantic validation to prevent malformed data. Note: the current authentication is a prototype; a real SAP BTP deployment would use OAuth2/OIDC.
