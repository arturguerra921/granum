# GranumDSS
**A Decision Support System for Agricultural Logistics and Optimization**

[![Build Status](https://img.shields.io/github/actions/workflow/status/arturguerra921/granum/main.yml?branch=main)](https://github.com/arturguerra921/granum/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/arturguerra921/granum)](https://github.com/arturguerra921/granum/blob/main/LICENSE)

## Overview
GranumDSS is a comprehensive Decision Support System (DSS) developed to optimize the allocation of agricultural products in warehouses, minimizing freight and storage costs. It processes complex agricultural supply chain data, calculates optimal routes, and estimates operational costs using advanced mathematical modeling alongside Open Source Routing Machine (OSRM) integration.

## Key Features
* **Distance Matrix Generation**: Computes exact distances and durations using OSRM for real road networks, falling back to Haversine calculations when necessary.
* **Cost Calculation**: Accurately evaluates transportation costs considering distance, freight rates, and minimum route thresholds.
* **Route Optimization**: Employs Mixed-Integer Linear Programming (MILP) using Pyomo and the CBC solver to calculate optimal product allocations between supply origins and destination warehouses.
* **Multilingual Dashboard**: Features an interactive web-based interface built with Dash, offering translations between English and Portuguese for enhanced accessibility.
* **Data Visualization**: Provides rich data insights, scenario filtering (e.g., Pareto 80/20 analysis), and optimization reports tailored for supply chain professionals.

## Why GranumDSS?
Managing agricultural logistics is a complex, high-stakes operational challenge. GranumDSS is designed specifically to aid planners and decision-makers in navigating these complexities. By leveraging mathematical optimization and Operations Research techniques, the system moves beyond simple spreadsheets. It rigorously evaluates thousands of product-warehouse combinations, respecting constraints such as warehouse capacity, minimum reception volumes, and upper flow limits.

The result is a structured, data-driven approach to scenario exploration. Decision-makers can visualize the impact of different logistics strategies, dynamically adjust parameters, and ultimately minimize the total costs associated with grain storage and transport—turning raw data into actionable enterprise intelligence.

## Technical Stack
* **Language**: Python 3.10+
* **Frontend/Dashboard**: Dash, Plotly, Dash Bootstrap Components
* **Optimization**: Pyomo (with the CBC solver)
* **Routing**: Open Source Routing Machine (OSRM), Requests
* **Data Processing**: Pandas, OpenPyXL

## Getting Started

### Using Docker (Recommended)
The easiest way to run GranumDSS alongside the required OSRM backend is via Docker Compose.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arturguerra921/granum.git
   cd granum
   ```

2. **Start the application and OSRM services:**
   ```bash
   docker-compose up -d --build
   ```

3. **Access the Application:**
   Open your browser and navigate to `http://localhost:8050`.

### Local Installation
If you prefer to run the application directly on your host machine:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arturguerra921/granum.git
   cd granum
   ```

2. **Install dependencies:**
   ```bash
   pip install .
   ```

3. **Run the server:**
   ```bash
   python run_server.py
   ```
*(Note: Running locally requires access to an OSRM instance. Set the `OSRM_URL` environment variable if your instance is not running on `http://localhost:5000`)*

## Project Structure
```
granum/
├── docker-compose.yml       # Docker services configuration
├── pyproject.toml           # Project dependencies and metadata
├── run_server.py            # Local execution script
├── wsgi.py                  # Gunicorn entry point for production
├── src/
│   ├── view/                # Dash frontend, layout, and components
│   ├── logic/               # Core business logic (OSRM, Optimization, i18n)
│   ├── locales/             # Translation files (en.json, pt.json)
│   └── assets/              # Static assets (images, CSS)
├── tests/                   # Backend test suite
├── benchmark/               # Benchmarking scripts and output
└── scripts/                 # Utility scripts for OSRM setup and benchmarking
```
