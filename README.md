# Player-injuries-and-team-performance-
# FootLens – Player Injuries and Team Performance Dashboard

## 1. Project Overview

This project is part of the **IBCP – Mathematics for AI-II** course and focuses on
building a **user-centred data dashboard** using **Streamlit**.

The dashboard analyses a football dataset containing:
- Player information
- Club and match details
- Injury dates and recovery periods
- Match outcomes and performance ratings

The aim is to help **technical directors, sports scientists, and analysts** understand
how injuries affect team performance and identify key risk and opportunity areas.

## 2. Research Questions

The analysis is driven by the following questions:

1. How do key player injuries impact overall team performance (points and goal difference) during their absence?
2. What is the team’s win/draw/loss record in matches where injured players were unavailable compared to when they were fully fit?
3. How do individual players’ performance ratings change before injury, during the injury-affected period, and after recovery?
4. Are there specific clubs or months where injury clusters are more frequent, and do these correlate with drops in performance?
5. Which clubs suffer the largest performance drop index due to injuries, and which players have the strongest “comeback” improvement after returning?

## 3. Dashboard Features

- **Interactive filters** for club, player, and season  
- **KPI cards** summarising:
  - Total injuries
  - Total matches
  - Average player rating
  - Average goal difference
- **Visual 1 – Bar Chart**: Top 10 injuries with highest team performance drop
- **Visual 2 – Line Chart**: Player rating timeline before, during, and after injury
- **Visual 3 – Heatmap**: Injury frequency by month and club
- **Visual 4 – Scatter Plot**: Player age vs performance drop index (if age available)
- **Visual 5 – Leaderboard Table**: Top “comeback” players by rating improvement

## 4. Tech Stack & Integration Details

- **Python**
- **Pandas** for data cleaning and feature engineering
- **NumPy** for numerical operations
- **Plotly Express** for interactive charts
- **Streamlit** for building and deploying the web dashboard

Data is loaded from a CSV file, preprocessed (date parsing, performance index calculation, injury phase labelling), and then presented through an interactive interface.

## 5. How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Streamlit app
streamlit run app.py
