import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from collections import defaultdict
from PIL import Image
import io

# DB setup
conn = sqlite3.connect("cricket_stats.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS stats (
    batsman TEXT,
    bowler TEXT,
    beaten INTEGER DEFAULT 0,
    wicket INTEGER DEFAULT 0,
    pace_wide INTEGER DEFAULT 0,
    spin_wide INTEGER DEFAULT 0,
    no_ball INTEGER DEFAULT 0,
    PRIMARY KEY (batsman, bowler)
)''')
conn.commit()

# Initialize session state
if "current_batsman" not in st.session_state:
    st.session_state.current_batsman = ""
if "bowlers" not in st.session_state:
    st.session_state.bowlers = []
if "last_batsman" not in st.session_state:
    st.session_state.last_batsman = ""

st.title("Cricket Performance Tracker")

# Add new batsman
batsman_name = st.text_input("Enter Batsman Name", st.session_state.current_batsman)
if batsman_name:
    if batsman_name != st.session_state.last_batsman:
        st.session_state.bowlers = []  # Clear bowlers list for new batsman
        st.session_state.last_batsman = batsman_name
    st.session_state.current_batsman = batsman_name

# Add new bowler
new_bowler = st.text_input("Add Bowler Name")
if st.button("Add Bowler") and new_bowler:
    if new_bowler not in st.session_state.bowlers:
        st.session_state.bowlers.append(new_bowler)

# Select bowler to update
selected_bowler = st.selectbox("Select Bowler to Update", st.session_state.bowlers)

# Counter buttons
if selected_bowler:
    st.markdown(f"### Stats for {selected_bowler} vs {st.session_state.current_batsman}")
    col1, col2, col3, col4, col5 = st.columns(5)

    def update_stat(column):
        c.execute(f"SELECT {column} FROM stats WHERE batsman=? AND bowler=?", 
                  (st.session_state.current_batsman, selected_bowler))
        row = c.fetchone()
        current_value = row[0] if row else 0
        if row:
            c.execute(f"UPDATE stats SET {column}=? WHERE batsman=? AND bowler=?", 
                      (current_value + 1, st.session_state.current_batsman, selected_bowler))
        else:
            c.execute("INSERT INTO stats (batsman, bowler, " + column + ") VALUES (?, ?, ?)", 
                      (st.session_state.current_batsman, selected_bowler, 1))
        conn.commit()

    if col1.button("Beaten"):
        update_stat("beaten")
    if col2.button("Wicket"):
        update_stat("wicket")
    if col3.button("Pace Wide"):
        update_stat("pace_wide")
    if col4.button("Spin Wide"):
        update_stat("spin_wide")
    if col5.button("No Ball"):
        update_stat("no_ball")

# Show counter summary for current batsman and bowler
if selected_bowler:
    st.markdown("#### Current Stats")
    current_stats = pd.read_sql_query("SELECT * FROM stats WHERE batsman=? AND bowler=?", conn, params=(st.session_state.current_batsman, selected_bowler))
    if not current_stats.empty:
        st.dataframe(current_stats.set_index(['batsman', 'bowler']))

# Generate visualization
st.markdown("### Generate Chart")
if st.button("Show Chart"):
    df = pd.read_sql_query("SELECT * FROM stats WHERE batsman=?", conn, params=(st.session_state.current_batsman,))
    if df.empty:
        st.warning("No data available for this batsman.")
    else:
        chart_data = df.set_index("bowler")[['beaten', 'wicket', 'pace_wide', 'spin_wide', 'no_ball']]
        total_beaten = int(chart_data['beaten'].sum())
        total_wickets = int(chart_data['wicket'].sum())

        colors = {
            'beaten': 'orange',
            'wicket': 'orangered',
            'pace_wide': 'deeppink',
            'spin_wide': 'magenta',
            'no_ball': 'deepskyblue'
        }

        ax = chart_data.plot(kind='bar', figsize=(10, 6), color=[colors[col] for col in chart_data.columns])
        plt.title(f"{st.session_state.current_batsman} vs Bowlers\nTotal Beaten: {total_beaten} | Total Wickets: {total_wickets}", fontsize=14, weight='bold')
        plt.ylabel("Count")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='')

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        image = Image.open(buf)
        st.image(image, caption=f"{st.session_state.current_batsman} vs Bowlers", use_column_width=True)
        buf.close()

# CSV Export
st.markdown("### Export Stats as CSV")
if st.button("Download CSV"):
    df_all = pd.read_sql_query("SELECT * FROM stats", conn)
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download All Stats as CSV",
        data=csv,
        file_name='cricket_stats.csv',
        mime='text/csv',
    )

# Consolidated stats for all batsmen
st.markdown("### Consolidated Stats for All Batsmen")
df_all = pd.read_sql_query("SELECT * FROM stats", conn)
if not df_all.empty:
    summary = df_all.groupby("batsman")[['beaten', 'wicket', 'pace_wide', 'spin_wide', 'no_ball']].sum()
    st.dataframe(summary)

conn.close()
