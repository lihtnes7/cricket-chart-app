import streamlit as st import pandas as pd import sqlite3

--- Database setup ---

conn = sqlite3.connect("cricket_stats.db", check_same_thread=False) cursor = conn.cursor()

Create tables

cursor.execute(''' CREATE TABLE IF NOT EXISTS players ( name TEXT PRIMARY KEY, type TEXT CHECK(type IN ('batsman', 'bowler')) ) ''')

cursor.execute(''' CREATE TABLE IF NOT EXISTS stats ( batsman TEXT, bowler TEXT, beaten INTEGER DEFAULT 0, wicket INTEGER DEFAULT 0, pace_wide INTEGER DEFAULT 0, spin_wide INTEGER DEFAULT 0, no_ball INTEGER DEFAULT 0, PRIMARY KEY (batsman, bowler) ) ''')

conn.commit()

--- Sidebar: Add Players ---

st.sidebar.header("Add Players") new_batsman = st.sidebar.text_input("New Batsman Name") if st.sidebar.button("Add Batsman"): if new_batsman: cursor.execute("INSERT OR IGNORE INTO players VALUES (?, 'batsman')", (new_batsman.strip(),)) conn.commit()

new_bowler = st.sidebar.text_input("New Bowler Name") if st.sidebar.button("Add Bowler"): if new_bowler: cursor.execute("INSERT OR IGNORE INTO players VALUES (?, 'bowler')", (new_bowler.strip(),)) conn.commit()

--- Main Title ---

st.title("🏏 Cricket Player Stats Tracker")

--- Batsman Selection ---

cursor.execute("SELECT name FROM players WHERE type='batsman'") batsmen = [row[0] for row in cursor.fetchall()] selected_batsman = st.selectbox("Select a Batsman to Edit/View Stats", batsmen)

if selected_batsman: cursor.execute("SELECT name FROM players WHERE type='bowler'") bowlers = [row[0] for row in cursor.fetchall()]

for bowler in bowlers:
    with st.expander(f"Stats vs {bowler}"):
        cursor.execute("SELECT * FROM stats WHERE batsman=? AND bowler=?", (selected_batsman, bowler))
        row = cursor.fetchone()
        current = {
            "beaten": row[2] if row else 0,
            "wicket": row[3] if row else 0,
            "pace_wide": row[4] if row else 0,
            "spin_wide": row[5] if row else 0,
            "no_ball": row[6] if row else 0,
        }

        beaten = st.number_input("Beaten Deliveries", min_value=0, value=current["beaten"], key=f"{bowler}_beaten")
        wicket = st.number_input("Wickets", min_value=0, value=current["wicket"], key=f"{bowler}_wicket")
        pace_wide = st.number_input("Pace Wides", min_value=0, value=current["pace_wide"], key=f"{bowler}_pace")
        spin_wide = st.number_input("Spin Wides", min_value=0, value=current["spin_wide"], key=f"{bowler}_spin")
        no_ball = st.number_input("No Balls", min_value=0, value=current["no_ball"], key=f"{bowler}_noball")

        if st.button("Save Stats", key=f"save_{bowler}"):
            cursor.execute('''
                INSERT OR REPLACE INTO stats
                (batsman, bowler, beaten, wicket, pace_wide, spin_wide, no_ball)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (selected_batsman, bowler, beaten, wicket, pace_wide, spin_wide, no_ball))
            conn.commit()
            st.success(f"Stats for {selected_batsman} vs {bowler} saved!")

--- Summary Table ---

st.subheader("📊 Summary of All Batsmen") cursor.execute(''' SELECT batsman, SUM(beaten) as Total_Beaten, SUM(wicket) as Total_Wickets, SUM(pace_wide) as Total_Pace_Wide, SUM(spin_wide) as Total_Spin_Wide, SUM(no_ball) as Total_No_Balls FROM stats GROUP BY batsman ''') summary_rows = cursor.fetchall()

if summary_rows: summary_df = pd.DataFrame(summary_rows, columns=[ "Batsman", "Total Beaten", "Total Wickets", "Total Pace Wides", "Total Spin Wides", "Total No Balls"]) st.dataframe(summary_df) else: st.info("No summary data available yet. Start by adding stats.")

