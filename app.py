import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- Database setup ---
conn = sqlite3.connect("cricket_stats.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    name TEXT PRIMARY KEY,
    type TEXT CHECK(type IN ('batsman'))
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS stats (
    batsman TEXT,
    bowler TEXT,
    beaten INTEGER DEFAULT 0,
    wicket INTEGER DEFAULT 0,
    pace_wide INTEGER DEFAULT 0,
    spin_wide INTEGER DEFAULT 0,
    no_ball INTEGER DEFAULT 0,
    PRIMARY KEY (batsman, bowler)
)
''')

conn.commit()

# --- Sidebar: Add Players ---
st.sidebar.header("Add Batsman")
new_batsman = st.sidebar.text_input("New Batsman Name")
if st.sidebar.button("Add Batsman"):
    if new_batsman:
        cursor.execute("INSERT OR IGNORE INTO players VALUES (?)", (new_batsman.strip(),))
        conn.commit()

# --- Main Title ---
st.title("🏏 Cricket Player Stats Tracker")

# --- Batsman Selection ---
cursor.execute("SELECT name FROM players")
batsmen = [row[0] for row in cursor.fetchall()]
selected_batsman = st.selectbox("Select a Batsman to Edit/View Stats", batsmen)

if selected_batsman:
    st.markdown("### Add Bowler and Enter Stats")
    bowler_name = st.text_input("Bowler Name")
    if bowler_name:
        cursor.execute("SELECT * FROM stats WHERE batsman=? AND bowler=?", (selected_batsman, bowler_name))
        row = cursor.fetchone()
        current = {
            "beaten": row[2] if row else 0,
            "wicket": row[3] if row else 0,
            "pace_wide": row[4] if row else 0,
            "spin_wide": row[5] if row else 0,
            "no_ball": row[6] if row else 0,
        }

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            beaten = st.number_input("Beaten", min_value=0, value=current["beaten"], key=f"{bowler_name}_beaten")
        with col2:
            wicket = st.number_input("Wickets", min_value=0, value=current["wicket"], key=f"{bowler_name}_wicket")
        with col3:
            pace_wide = st.number_input("Pace Wide", min_value=0, value=current["pace_wide"], key=f"{bowler_name}_pace")
        with col4:
            spin_wide = st.number_input("Spin Wide", min_value=0, value=current["spin_wide"], key=f"{bowler_name}_spin")
        with col5:
            no_ball = st.number_input("No Balls", min_value=0, value=current["no_ball"], key=f"{bowler_name}_noball")

        if st.button("Save Stats", key=f"save_{bowler_name}"):
            cursor.execute('''
                INSERT OR REPLACE INTO stats
                (batsman, bowler, beaten, wicket, pace_wide, spin_wide, no_ball)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (selected_batsman, bowler_name, beaten, wicket, pace_wide, spin_wide, no_ball))
            conn.commit()
            st.success(f"Stats for {selected_batsman} vs {bowler_name} saved!")

# --- Visualization ---
st.subheader("📈 Visualize Batsman's Stats")
selected_batsman_viz = st.selectbox("Select a Batsman to Visualize", batsmen, key="viz")
if selected_batsman_viz:
    df_viz = pd.read_sql_query("SELECT * FROM stats WHERE batsman = ?", conn, params=(selected_batsman_viz,))
    if not df_viz.empty:
        df_melt = df_viz.melt(id_vars=["bowler"], value_vars=["beaten", "wicket", "pace_wide", "spin_wide", "no_ball"], 
                              var_name="Metric", value_name="Count")

        chart = alt.Chart(df_melt).mark_bar().encode(
            x=alt.X('bowler:N', title="Bowler"),
            y=alt.Y('Count:Q'),
            color='Metric:N',
            column='Metric:N'
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data to visualize for this batsman.")

# --- Summary Table ---
st.subheader("📊 Summary of All Batsmen")
cursor.execute('''
    SELECT batsman, SUM(beaten) as Total_Beaten, SUM(wicket) as Total_Wickets,
           SUM(pace_wide) as Total_Pace_Wide, SUM(spin_wide) as Total_Spin_Wide, SUM(no_ball) as Total_No_Balls
    FROM stats
    GROUP BY batsman
''')
summary_rows = cursor.fetchall()

if summary_rows:
    summary_df = pd.DataFrame(summary_rows, columns=[
        "Batsman", "Total Beaten", "Total Wickets", "Total Pace Wides", "Total Spin Wides", "Total No Balls"])
    st.dataframe(summary_df)
else:
    st.info("No summary data available yet. Start by adding stats.")
