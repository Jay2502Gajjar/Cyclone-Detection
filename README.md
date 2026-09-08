# CycloVision — Tropical Cyclone Intelligence & Early Warning Platform

![CycloVision Platform](https://img.shields.io/badge/System-Active-emerald?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20TS-61DAFB?style=for-the-badge)
![Spring Boot](https://img.shields.io/badge/Backend-Spring%20Boot%203-6DB33F?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/AI%20Service-FastAPI%20%7C%20PyTorch-009688?style=for-the-badge)

CycloVision is a multi-modal AI platform for tropical cyclone detection, intensity classification, spatial trajectory forecasting, risk assessment, and disaster decision support.

---

## Key Features

1. **Interactive Earth Wind Particle Visualizer Canvas**: Inspired by [earth.nullschool.net](https://earth.nullschool.net/), real-time HTML5 vector particle animation overlay simulating wind velocity streams around cyclone eye centers.
2. **AI Vision & Grad-CAM Heatmaps**: PyTorch ResNet-34 transfer learning model detecting cyclone formation, eye center closure, and class activation maps.
3. **Trajectory & Intensity Forecast Engine**: Hybrid Kalman Filter state extrapolator (6h-12h) + XGBoost spatiotemporal net (24h-48h) with visual uncertainty cones.
4. **KNN Historical Storm Similarity Engine**: Nearest Neighbors matching against 10,000+ IBTrACS cyclone track embeddings to provide analog storm outcomes (e.g. Cyclone Fani, Amphan, Tauktae).
5. **Rule-Based Coastal Risk Scoring**: Spatial risk formula calculating threat levels (Critical, High, Moderate, Low) based on landfall proximity, central pressure deficit, and sustained wind speed.
6. **Automated AI Situation Reports**: Emergency operational briefs outlining hazards, evacuation zones, and response actions.

---

## System Architecture

```text
React Frontend (Vite + TS + Tailwind + Leaflet + Wind Canvas)
       │
       ▼ REST APIs
Spring Boot Backend (Java 17, JPA, Risk Engine, Fallback Data Seeder)
       │
       ▼ HTTP
FastAPI AI Service (PyTorch ResNet, XGBoost, Kalman Filter, KNN Engine)
```

---

## Quick Start & Execution

### 1. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Dashboard opens on http://localhost:5173
```

### 2. Backend Service
```bash
cd backend
mvnw.cmd spring-boot:run
# Spring Boot API runs on http://localhost:8080
```

### 3. AI Inference Service
```bash
cd ai-service
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
# FastAPI swagger docs available at http://localhost:8000/docs
```

### 4. Docker (All-in-One)
```bash
docker compose up -d
```
