import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# -------------------
# CONFIG
# -------------------
st.set_page_config(
    page_title="FootLens – Player Injuries & Team Performance",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("player_injuries_impact.csv")
    return df

    # TODO: replace with your actual file name
    df = pd.read_csv("player_injuries_impact.csv")

    # ---- BASIC CLEANING ----
    date_cols = ["match_date", "injury_start", "injury_end"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Example column assumptions – EDIT to match your dataset
    # match_result: "W", "D", "L"
    # goals_for, goals_against: numeric
    df["goal_diff"] = df["goals_for"] - df["goals_against"]

    # Make sure rating column is numeric
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # Drop rows with no match_date
    df = df.dropna(subset=["match_date"])

    # ---- INJURY PHASE LABELS ----
    def label_phase(row):
        start = row["injury_start"]
        end = row["injury_end"]
        match_date = row["match_date"]

        if pd.isna(start) or pd.isna(end):
            return "No recorded injury"

        if match_date < start:
            return "Before injury"
        elif start <= match_date <= end:
            return "During unfit / absence"
        else:
            return "After return"

    df["phase"] = df.apply(label_phase, axis=1)

    # Player age: if not included, comment this
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")

    return df

df = load_data()

st.title("⚽ FootLens Analytics – Player Injuries & Team Performance Dashboard")
st.markdown(
    """
This dashboard helps technical directors and analysts understand **how player injuries impact team performance**,
match outcomes, and player comebacks.
"""
)

# -------------------
# SIDEBAR FILTERS
# -------------------
st.sidebar.header("Filters")

clubs = sorted(df["Team Name"].dropna().unique())
players = sorted(df["Name"].dropna().unique())
seasons = sorted(df["season"].dropna().unique()) if "season" in df.columns else []

selected_club = st.sidebar.selectbox("Select Club", options=["All"] + clubs)
selected_player = st.sidebar.selectbox("Highlight Player (optional)", options=["None"] + players)
selected_season = st.sidebar.selectbox("Season (optional)", options=["All"] + seasons) if len(seasons) > 0 else "All"

filtered_df = df.copy()
if selected_club != "All":
    filtered_df = filtered_df[filtered_df["club"] == selected_club]

if selected_season != "All" and "season" in df.columns:
    filtered_df = filtered_df[filtered_df["season"] == selected_season]


# -------------------
# KPI CARDS (FIXED)
# -------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_injuries = filtered_df["Injury"].notna().sum()
    st.metric("Total Injuries (filtered)", total_injuries)

with col2:
    # Some datasets don’t have explicit match IDs — we approximate
    match_columns = [col for col in filtered_df.columns if "Match" in col and "Result" in col]
    total_matches = len(match_columns)
    st.metric("Total Match-related Fields", total_matches)

with col3:
    avg_rating_cols = [col for col in filtered_df.columns if "rating" in col.lower()]
    avg_rating = filtered_df[avg_rating_cols].apply(pd.to_numeric, errors='coerce').stack().mean()
    st.metric("Avg Player Rating", f"{avg_rating:.2f}" if not pd.isna(avg_rating) else "N/A")

with col4:
    st.metric("Dataset Rows (Injury Records)", len(filtered_df))



st.markdown("---")

# =====================================================
# VISUAL 1: Top 10 injuries with highest performance drop (Bar Chart)
# =====================================================
st.subheader("1. Top Injuries with Highest Team Performance Drop")

if {"Name", "Team Name", "Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"}.issubset(df.columns):
    perf_df = df[["Name", "Team Name", "Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"]].copy()

    perf_df["Match1_before_injury_Player_rating"] = pd.to_numeric(perf_df["Match1_before_injury_Player_rating"], errors="coerce")
    perf_df["Match1_after_injury_Player_rating"] = pd.to_numeric(perf_df["Match1_after_injury_Player_rating"], errors="coerce")

    perf_df["Performance Drop"] = perf_df["Match1_before_injury_Player_rating"] - perf_df["Match1_after_injury_Player_rating"]
    perf_df = perf_df.dropna(subset=["Performance Drop"])

    top_drops = perf_df.sort_values("Performance Drop", ascending=False).head(10)

    fig1 = px.bar(top_drops,
                  x="Name",
                  y="Performance Drop",
                  color="Team Name",
                  title="Top 10 Players with Highest Performance Drop After Injury")
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("Required columns for performance drop analysis are missing.")


# =====================================================
# VISUAL 2: Player performance timeline (Line Chart)
# =====================================================
st.subheader("2. Player Performance Timeline – Before vs After Injury")

if {"Name", "Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"}.issubset(df.columns):
    avg_perf = df.groupby("Name")[["Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"]].mean().reset_index()

    melted = avg_perf.melt(id_vars="Name", var_name="Phase", value_name="Rating")

    fig2 = px.bar(melted, x="Name", y="Rating", color="Phase", title="Average Rating Before vs After Injury")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Required columns for before/after comparison are missing.")


# =====================================================
# VISUAL 3: Heatmap – Injury frequency across months and clubs
# =====================================================
st.subheader("3. Injury Frequency by Month and Club (Heatmap)")

if {"Date of Injury", "Team Name"}.issubset(df.columns):
    df["Date of Injury"] = pd.to_datetime(df["Date of Injury"], errors="coerce")
    df["Month"] = df["Date of Injury"].dt.strftime("%b")

    heat_df = df.groupby(["Team Name", "Month"]).size().reset_index(name="Injury Count")

    fig3 = px.density_heatmap(heat_df, x="Month", y="Team Name", z="Injury Count",
                              color_continuous_scale="Reds",
                              title="Injury Frequency by Month and Team")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Columns 'Date of Injury' or 'Team Name' are missing.")


# =====================================================
# VISUAL 4: Scatter – Player age vs performance drop index
# =====================================================
st.subheader("4. Player Age vs Performance Drop Index")

st.subheader("4. Player Age vs Performance Drop Index")

if {"Age", "Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"}.issubset(df.columns):
    df["Match1_before_injury_Player_rating"] = pd.to_numeric(df["Match1_before_injury_Player_rating"], errors="coerce")
    df["Match1_after_injury_Player_rating"] = pd.to_numeric(df["Match1_after_injury_Player_rating"], errors="coerce")
    df["Performance Drop"] = df["Match1_before_injury_Player_rating"] - df["Match1_after_injury_Player_rating"]

    fig4 = px.scatter(df, x="Age", y="Performance Drop", color="Team Name", hover_data=["Name"],
                      title="Player Age vs Performance Drop After Injury")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("Age or rating columns missing; cannot plot age vs performance drop.")


# =====================================================
# VISUAL 5: Leaderboard – Comeback players by rating improvement
# =====================================================
st.subheader("5. Comeback Leaderboard – Rating Improvement After Injury")

if {"Name", "Team Name", "Match1_before_injury_Player_rating", "Match1_after_injury_Player_rating"}.issubset(df.columns):
    comeback = df.copy()
    comeback["Match1_before_injury_Player_rating"] = pd.to_numeric(comeback["Match1_before_injury_Player_rating"], errors="coerce")
    comeback["Match1_after_injury_Player_rating"] = pd.to_numeric(comeback["Match1_after_injury_Player_rating"], errors="coerce")
    comeback["Improvement"] = comeback["Match1_after_injury_Player_rating"] - comeback["Match1_before_injury_Player_rating"]

    leaderboard = comeback.sort_values("Improvement", ascending=False)[["Name", "Team Name", "Improvement"]].head(10)
    st.dataframe(leaderboard.style.format({"Improvement": "{:.2f}"}))
else:
    st.warning("Required columns for comeback leaderboard are missing.")

