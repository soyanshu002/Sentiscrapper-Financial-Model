# SentiScrapper: Advanced Multi-Agent Stock Forecasting & Sentiment System

SentiScrapper is a production-grade, multi-agent AI financial forecasting application. It aggregates historical price charts, technical signals, macroeconomic data, and social media/news sentiment (mined from Reddit, Twitter, Telegram, and Moneycontrol) to generate predictions and portfolio recommendations for equities.

Designed with industry standards, this repository provides a clean FastAPI backend and a responsive, high-fidelity React dashboard interface.

---

## 🌟 Key Features

1. **Multi-Agent Orchestration**:
   - **Data Agent**: Automatically fetches ticker histories and FRED macroeconomic factors.
   - **Sentiment Agent**: Harvests textual feeds, executes VADER polarity scoring, and builds decay-weighted indicators.
   - **Quant Analyst Agent**: Handles feature cleaning, runs KNN imputations, fits Random Forest/LSTM models, and makes multi-day forecasts.
   - **Portfolio Manager Agent**: Aggregates quant forecasts and technical indicators to compile trading advice reports.
2. **Double Predictive Engine**: Support for standard **Random Forest Regression** and deep-learning **LSTM Networks** leveraging local GPU execution.
3. **Robust Scraper Failover**: Scrapers are written to fall back automatically to realistic stock-specific mock simulations when API keys are missing or endpoints are rate-limited.
4. **Interactive Dashboard**: A custom dark-themed UI featuring historical/predicted price charts, sentiment metrics, and a real-time agent console showing the live agent execution steps.

---

## 📂 Project Architecture

```text
SentiScrapper Financial Analysis/
├── backend/
│   ├── app/
│   │   ├── config.py             # Loads settings, directory creators & API secrets from .env
│   │   ├── main.py               # FastAPI server defining schemas and endpoints (/api/analyze)
│   │   ├── scrapers/             # Web harvesting and financial fetchers
│   │   │   ├── market.py         # yfinance ticker fetcher & technical indicator equations (RSI, MACD)
│   │   │   ├── macro.py          # FRED inflation (CPI) and unemployment data via pandas_datareader
│   │   │   ├── reddit.py         # PRAW/asyncpraw scraper with keyword search fallback
│   │   │   ├── twitter.py        # Tweepy client interface
│   │   │   ├── telegram.py       # Telethon swing trade parser with non-blocking session validator
│   │   │   └── news.py           # BeautifulSoup4 scraping of Moneycontrol tags
│   │   ├── models/               # Mathematical modeling
│   │   │   ├── sentiment.py      # VADER polarity calculation + decay weighted sentiment factor
│   │   │   └── forecaster.py     # RF & LSTM pipelines (scaler savings, KNN Imputer, GPU toggling)
│   │   └── agents/               # Autonomous execution layer
│   │       └── orchestrator.py   # Multi-agent workflow runner (Data -> Sentiment -> Quant -> Manager)
│   ├── requirements.txt          # Explicitly pinned backend dependencies
│   └── run.py                    # Dev server startup launcher
├── frontend/                     # Modern React + Vite Single Page Application
├── .env.example                  # Environment secrets template
├── .env                          # Local secrets config (secrets, ports, model paths)
└── README.md                     # This file
```

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* (Optional) NVIDIA GPU with CUDA installed for accelerated TensorFlow LSTM execution.

### Backend Installation & Setup
1. Clone this repository and navigate to the root directory.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Adjust API keys inside `.env` if available (e.g. Reddit PRAW keys, Twitter bearer token). If left blank, the application automatically runs in **simulation mode** for social sentiment.

### Booting the Backend
Run the backend server:
```bash
python backend/run.py
```
The FastAPI documentation will be available at `http://127.0.0.1:8000/docs`.

### Frontend Installation & Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to the printed URL (typically `http://localhost:5173`).

---

## 📊 Technical Details
For an in-depth breakdown of the feature engineering, weighted sentiment decay formulas, machine learning models, GPU configuration, and common interview questions, please refer to the **[Technical Revision Guide](interview_prep.md)**.
