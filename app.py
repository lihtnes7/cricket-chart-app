import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Cricket Tracker", layout="wide")
st.title("🏏 Cricket Stats Tracker: Batsman vs Bowler")

CATEGORIES = ["Beaten", "Wicket", "Pace Wide", "Spin Wide", "No Ball"]

# Persistent session state
if "stats" not in st.session_state:
    st.session_state.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
if "batsmen" not in st.session_state:
    st.session_state.batsmen = []
if "bowlers" not in st.session_state:
    st.session_state.bowlers = []

# Add Batsman
st.sidebar.header("➕ Add Batsman")
new_batsman = st.sidebar.text_input("Batsman Name", key="batsman_input")
if st.sidebar.button("Add Batsman") and new_batsman:
    if new_batsman not in st.session_state.batsmen:
        st.session_state.batsmen.append(new_batsman.strip())

# Add Bowler
st.sidebar.header("➕ Add Bowler")
new_bowler = st.sidebar.text_input("Bowler Name", key="bowler_input")
if st.sidebar.button("Add Bowler") and new_bowler:
    if new_bowler not in st.session_state.bowlers:
        st.session_state.bowlers.append(new_bowler.strip())

# Guard Clause
if not st.session_state.batsmen or not st.session_state.bowlers:
    st.info("Please add at least one batsman and one bowler to begin.")
    st.stop()

# Choose batsman to update
selected_batsman = st.selectbox("🎯 Select Batsman", st.session_state.batsmen)

st.subheader(f"🔄 Delivery Tracking for: {selected_batsman}")
for bowler in st.session_state.bowlers:
    with st.expander(f"🎳 {bowler}"):
        cols = st.columns(len(CATEGORIES))
        for i, cat in enumerate(CATEGORIES):
            key = f"{selected_batsman}_{bowler}_{cat}"
            current_val = st.session_state.stats[selected_batsman][bowler][cat]
            updated_val = cols[i].number_input(
                label=cat,
                min_value=0,
                step=1,
                value=current_val,
                key=key
            )
            st.session_state.stats[selected_batsman][bowler][cat] = updated_val

# Generate and display table
st.subheader("📊 Summary Table")

data = []
for bowler in st.session_state.bowlers:
    stats = st.session_state.stats[selected_batsman][bowler]
    row = {"Bowler": bowler}
    row.update({cat: stats[cat] for cat in CATEGORIES})
    data.append(row)

df = pd.DataFrame(data)
total_beaten = df["Beaten"].sum()
total_wickets = df["Wicket"].sum()

st.dataframe(df, use_container_width=True)

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(df))
bar_w = 0.15

for i, cat in enumerate(CATEGORIES):
    ax.bar([xi + (i - 2) * bar_w for xi in x], df[cat], width=bar_w, label=cat)

ax.set_xticks(list(x))
ax.set_xticklabels(df["Bowler"])
ax.set_ylabel("Count")
ax.set_title(f"{selected_batsman} vs Bowlers")
ax.text(
    x=(len(df)-1)/2,
    y=df[CATEGORIES].values.max() + 1 if not df.empty else 1,
    s=f"Total Beaten: {total_beaten} | Total Wickets: {total_wickets}",
    ha="center",
    fontweight="bold"
)
ax.legend()
st.pyplot(fig)

# Export CSV
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("💾 Download CSV", csv, file_name=f"{selected_batsman}_stats.csv", mime="text/csv")
