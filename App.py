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
# KPI CARDS
# -------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_injuries = filtered_df["Injury"].nunique() if "Injury" in filtered_df.columns else filtered_df["Date of Injury"].notna().sum()
    st.metric("Total Injuries (filtered)", total_injuries)

with col2:
    # Estimate total matches from the available match columns
match_columns = [col for col in filtered_df.columns if "Match" in col and "Result" in col]
total_matches = len(match_columns)

with col3:
    avg_rating = filtered_df["rating"].mean()
    st.metric("Avg Player Rating", f"{avg_rating:.2f}" if not np.isnan(avg_rating) else "N/A")

with col4:
    mean_goal_diff = filtered_df["goal_diff"].mean()
    st.metric("Avg Goal Difference", f"{mean_goal_diff:.2f}" if not np.isnan(mean_goal_diff) else "N/A")


st.markdown("---")

# =====================================================
# VISUAL 1: Top 10 injuries with highest performance drop (Bar Chart)
# =====================================================
st.subheader("1. Top Injuries with Highest Team Performance Drop")

# Example logic:
# groupby injury / player: compare team goal_diff before vs during absence
if {"injury_start", "injury_end", "club", "goal_diff"}.issubset(df.columns):

    # For simplicity, approximate: use matches within X days before/after injury
    window_days = 30

    injury_rows = df.dropna(subset=["injury_start", "injury_end"]).copy()
    records = []

    for idx, row in injury_rows.iterrows():
        player = row["player_name"]
        club = row["club"]
        start = row["injury_start"]
        end = row["injury_end"]

        club_matches = df[df["club"] == club]

        before_mask = (club_matches["match_date"] >= (start - pd.Timedelta(days=window_days))) & \
                      (club_matches["match_date"] < start)
        during_mask = (club_matches["match_date"] >= start) & \
                      (club_matches["match_date"] <= end)

        before_perf = club_matches.loc[before_mask, "goal_diff"].mean()
        during_perf = club_matches.loc[during_mask, "goal_diff"].mean()

        if not (np.isnan(before_perf) or np.isnan(during_perf)):
            perf_drop = before_perf - during_perf
            records.append({
                "player_name": player,
                "club": club,
                "injury_start": start,
                "injury_end": end,
                "before_perf": before_perf,
                "during_perf": during_perf,
                "performance_drop_index": perf_drop
            })

    impact_df = pd.DataFrame(records)
    if not impact_df.empty:
        top_impacts = impact_df.sort_values("performance_drop_index", ascending=False).head(10)

        fig1 = px.bar(
            top_impacts,
            x="player_name",
            y="performance_drop_index",
            color="club",
            hover_data=["before_perf", "during_perf", "injury_start", "injury_end"],
            title="Top 10 Injuries by Performance Drop Index"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Not enough data to compute performance drop index.")
else:
    st.warning("Required columns for performance drop analysis are missing.")


# =====================================================
# VISUAL 2: Player performance timeline (Line Chart)
# =====================================================
st.subheader("2. Player Performance Timeline – Before vs After Injury")

if selected_player != "None":
    player_df = filtered_df[filtered_df["player_name"] == selected_player].sort_values("match_date")
    if not player_df.empty:
        fig2 = px.line(
            player_df,
            x="match_date",
            y="rating",
            color="phase",
            title=f"Rating Timeline for {selected_player}",
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No matches for the selected player with current filters.")
else:
    st.info("Select a player in the sidebar to view their performance timeline.")


# =====================================================
# VISUAL 3: Heatmap – Injury frequency across months and clubs
# =====================================================
st.subheader("3. Injury Frequency by Month and Club (Heatmap)")

if "injury_start" in df.columns and "club" in df.columns:
    inj = df.dropna(subset=["injury_start"]).copy()
    inj["month"] = inj["injury_start"].dt.to_period("M").astype(str)

    heat_df = inj.groupby(["club", "month"]).size().reset_index(name="injury_count")
    if not heat_df.empty:
        fig3 = px.density_heatmap(
            heat_df,
            x="month",
            y="club",
            z="injury_count",
            color_continuous_scale="Reds",
            title="Injury Count Heatmap (Month x Club)"
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No injury data available for heatmap.")
else:
    st.warning("Columns 'injury_start' or 'club' missing.")


# =====================================================
# VISUAL 4: Scatter – Player age vs performance drop index
# =====================================================
st.subheader("4. Player Age vs Performance Drop Index")

if "age" in df.columns and not df["age"].isna().all():
    if 'performance_drop_index' in locals() or 'impact_df' in locals():
        if 'impact_df' in locals() and not impact_df.empty:
            age_merge = impact_df.merge(
                df[["player_name", "age"]].drop_duplicates(),
                on="player_name",
                how="left"
            )
            fig4 = px.scatter(
                age_merge,
                x="age",
                y="performance_drop_index",
                color="club",
                hover_data=["player_name"],
                title="Age vs Performance Drop Index"
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Performance impact data not available yet for scatter plot.")
    else:
        st.info("Run the performance impact calculation above first.")
else:
    st.warning("Age column missing or empty; cannot plot age vs performance drop.")


# =====================================================
# VISUAL 5: Leaderboard – Comeback players by rating improvement
# =====================================================
st.subheader("5. Comeback Leaderboard – Rating Improvement After Injury")

if {"player_name", "rating", "phase"}.issubset(df.columns):
    # average rating per player in each phase
    phase_stats = df.groupby(["player_name", "club", "phase"])["rating"].mean().reset_index()

    before = phase_stats[phase_stats["phase"] == "Before injury"][["player_name", "club", "rating"]]
    after = phase_stats[phase_stats["phase"] == "After return"][["player_name", "rating"]]

    before = before.rename(columns={"rating": "rating_before"})
    after = after.rename(columns={"rating": "rating_after"})

    merged = before.merge(after, on="player_name", how="inner")
    merged["rating_change"] = merged["rating_after"] - merged["rating_before"]

    comeback = merged.sort_values("rating_change", ascending=False).head(10)

    st.dataframe(comeback.style.format({
        "rating_before": "{:.2f}",
        "rating_after": "{:.2f}",
        "rating_change": "{:.2f}"
    }))
else:
    st.warning("Required columns for comeback leaderboard are missing.")
