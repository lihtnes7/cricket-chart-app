import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import matplotlib.pyplot as plt
from io import BytesIO

# --- Database setup ---
conn = sqlite3.connect("cricket_stats.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS players (
    name TEXT PRIMARY KEY
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

# --- App Title ---
st.set_page_config(layout="wide")
st.title("🏏 Cricket Player Stats Tracker")

# --- Add and Select Batsman ---
st.markdown("### Add or Select Batsman")
col_a, col_b = st.columns([2, 3])
with col_a:
    new_batsman = st.text_input("New Batsman Name")
    if st.button("Add Batsman"):
        if new_batsman:
            cursor.execute("INSERT OR IGNORE INTO players VALUES (?)", (new_batsman.strip(),))
            conn.commit()
            st.success(f"Added new batsman: {new_batsman}")

cursor.execute("SELECT name FROM players")
batsmen = [row[0] for row in cursor.fetchall()]
with col_b:
    selected_batsman = st.selectbox("Select Batsman to Edit/View Stats", batsmen)

# --- Enter Bowler Stats ---
if selected_batsman:
    st.markdown("### Add or Modify Bowler Stats")
    cursor.execute("SELECT bowler FROM stats WHERE batsman = ?", (selected_batsman,))
    existing_bowlers = [row[0] for row in cursor.fetchall()]

    bowler_option = st.selectbox("Select Existing Bowler or Add New", existing_bowlers + ["Add New Bowler"])
    if bowler_option == "Add New Bowler":
        new_bowler = st.text_input("Enter New Bowler Name")
        bowler_name = new_bowler.strip() if new_bowler else None
    else:
        bowler_name = bowler_option

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

        with st.expander(f"Stats for {bowler_name} vs {selected_batsman}", expanded=False):
            col1, col2, col3, col4, col5 = st.columns(5)
            beaten = col1.number_input("Beaten", min_value=0, value=current["beaten"], key=f"{bowler_name}_beaten")
            wicket = col2.number_input("Wickets", min_value=0, value=current["wicket"], key=f"{bowler_name}_wicket")
            pace_wide = col3.number_input("Pace Wide", min_value=0, value=current["pace_wide"], key=f"{bowler_name}_pace")
            spin_wide = col4.number_input("Spin Wide", min_value=0, value=current["spin_wide"], key=f"{bowler_name}_spin")
            no_ball = col5.number_input("No Balls", min_value=0, value=current["no_ball"], key=f"{bowler_name}_noball")

            # Auto-save on change
            cursor.execute('''
                INSERT OR REPLACE INTO stats
                (batsman, bowler, beaten, wicket, pace_wide, spin_wide, no_ball)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (selected_batsman, bowler_name, beaten, wicket, pace_wide, spin_wide, no_ball))
            conn.commit()
            st.info("Auto-saved stats on change")

# --- Visualization as Image ---
st.markdown("### 📊 Visualize Batsman's Stats as Image")
selected_batsman_viz = st.selectbox("Select a Batsman to Visualize", batsmen, key="viz")
if selected_batsman_viz:
    df_viz = pd.read_sql_query("SELECT * FROM stats WHERE batsman = ?", conn, params=(selected_batsman_viz,))
    if not df_viz.empty:
        total_beaten = df_viz['beaten'].sum()
        total_wickets = df_viz['wicket'].sum()

        st.markdown(f"**Beaten:** {total_beaten} | **Wickets:** {total_wickets}")

        metrics = ['beaten', 'wicket', 'pace_wide', 'spin_wide', 'no_ball']
        fig, axes = plt.subplots(nrows=1, ncols=len(metrics), figsize=(4 * len(metrics), 4))
        for ax, metric in zip(axes, metrics):
            ax.bar(df_viz['bowler'], df_viz[metric])
            ax.set_title(metric.replace("_", " ").title())
            ax.set_xticklabels(df_viz['bowler'], rotation=45, ha='right')

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png")
        st.image(buf.getvalue(), caption=f"Stats Image for {selected_batsman_viz}", use_column_width=True)
        buf.close()
        plt.close(fig)
    else:
        st.info("No data to visualize for this batsman.")

# --- Summary Table ---
st.markdown("### 🧾 Summary of All Batsmen")
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
