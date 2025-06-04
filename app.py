import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Cricket Batsman vs Bowlers Analysis")
st.markdown("""
Enter batsman's sequence (use `2` for beaten, `5` for wicket).

Enter each bowler's delivery result using:
- `b` for beaten
- `w` for wicket
- `1` for pace wide
- `2` for spin wide
- `3` for no ball

Separate entries with spaces. Example: `2 b b w`
""")

# Input: batsman sequence
batsman_name = st.text_input("Batsman Name", "Vince")
batting_seq = st.text_input("Batting Sequence", "2 2 2 5 2 2 5 2 2 5")

# Process batsman data
batting_list = batting_seq.strip().split()
batsman_beaten = batting_list.count("2")
batsman_wickets = batting_list.count("5")

# Input: Bowler data
bowlers = {}
bowler_names = st.text_area("Enter bowler names (one per line)", "Hari\nMano\nPraveen\nDurai\nRenga\nadi\nRazeeth\nShyam").splitlines()

for bowler in bowler_names:
    event_str = st.text_input(f"{bowler} - deliveries", "")
    events = event_str.strip().split()
    bowlers[bowler] = {
        "Beaten (b)": events.count("b"),
        "Wickets (w)": events.count("w"),
        "Pace Wides (1)": events.count("1"),
        "Spin Wides (2)": events.count("2"),
        "No Balls (3)": events.count("3")
    }

# Build DataFrame
df = pd.DataFrame.from_dict(bowlers, orient="index")
df.reset_index(inplace=True)
df.rename(columns={"index": "Bowler"}, inplace=True)

# Plot chart
if not df.empty:
    df.fillna(0, inplace=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_w = 0.15
    x = range(len(df))

    ax.bar([i - 2 * bar_w for i in x], df["Beaten (b)"], width=bar_w, label="Beaten (b)", color="skyblue")
    ax.bar([i - 1 * bar_w for i in x], df["Wickets (w)"], width=bar_w, label="Wickets (w)", color="salmon")
    ax.bar([i for i in x], df["Pace Wides (1)"], width=bar_w, label="Pace Wides (1)", color="lightgreen")
    ax.bar([i + 1 * bar_w for i in x], df["Spin Wides (2)"], width=bar_w, label="Spin Wides (2)", color="violet")
    ax.bar([i + 2 * bar_w for i in x], df["No Balls (3)"], width=bar_w, label="No Balls (3)", color="orange")

    ax.set_xticks(x)
    ax.set_xticklabels(df["Bowler"])
    ax.set_xlabel("Bowler")
    ax.set_ylabel("Count")
    ax.set_title(f"{batsman_name}'s Batting: Beaten, Wickets & Extras")

    # Annotate total at top
    max_h = df[["Beaten (b)", "Wickets (w)", "Pace Wides (1)", "Spin Wides (2)", "No Balls (3)"]].max().max()
    ax.text(
        x=(len(df)-1)/2,
        y=max_h + 0.5,
        s=f"Total Beaten: {batsman_beaten}   Total Wickets: {batsman_wickets}",
        ha="center",
        fontweight="bold"
    )

    ax.legend()
    st.pyplot(fig)
else:
    st.warning("Enter at least one bowler's data to generate the chart.")
