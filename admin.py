import streamlit as st
import pandas as pd
import plotly.express as px
from remotetech_data import (
    init_db,
    get_all_student_progress,
    get_inactive_students,
    get_quest_completion_stats,
)

init_db()

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

if st.session_state.get("user_name") != "admin":
    st.error("⛔ You do not have permission to view this page.")
    st.stop()

st.set_page_config(page_title="Admin Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Teacher / Admin Dashboard")
st.caption("RemoteTech Sterkspruit Pilot — Class Overview")

students    = get_all_student_progress()
quest_stats = get_quest_completion_stats()
inactive    = get_inactive_students(days=7)

# ====================== TOP METRICS ======================
total_students  = len(students)
completed_all   = sum(1 for s in students if s["lessons_count"] >= 6)
avg_points      = round(sum(s["points"] for s in students) / total_students, 1) if total_students else 0
inactive_count  = len(inactive)

col1, col2, col3, col4 = st.columns(4)
col1.metric("👩‍🎓 Total Students",       total_students)
col2.metric("🎓 Completed All Quests",   completed_all)
col3.metric("⭐ Avg Points",             avg_points)
col4.metric("😴 Inactive (7+ days)",     inactive_count,
            delta=f"-{inactive_count}" if inactive_count else None,
            delta_color="inverse")

st.divider()

# ====================== STUDENT PROGRESS TABLE ======================
st.subheader("📋 All Students")

search = st.text_input("🔍 Search by name or username", "")
rows = []
for s in students:
    if search.lower() in s["full_name"].lower() or search.lower() in s["user_name"].lower():
        rows.append({
            "Name":         s["full_name"],
            "Username":     s["user_name"],
            "Points":       s["points"],
            "Quests Done":  f"{s['lessons_count']} / 6",
            "Badges":       ", ".join(s["badges"]) if s["badges"] else "None",
            "Last Active":  s["last_active"] or "Never",
            "Status":       "✅ Complete"   if s["lessons_count"] >= 6
                            else ("⚠️ In Progress" if s["lessons_count"] > 0
                            else "🔴 Not Started"),
        })

if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export as CSV", csv, "student_progress.csv", "text/csv")
else:
    st.info("No students found.")

st.divider()

# ====================== QUEST COMPLETION CHART ======================
st.subheader("📊 Quest Completion Rates")

QUEST_LABELS = {
    "1": "Quest 1: Variables",
    "2": "Quest 2: Taxi Fare",
    "3": "Quest 3: Decisions",
    "4": "Quest 4: Loops",
    "5": "Quest 5: Functions",
    "6": "Quest 6: List Magic",
}

quest_df = pd.DataFrame([
    {"Quest": QUEST_LABELS[k], "Students Completed": v}
    for k, v in quest_stats.items()
])

fig = px.bar(
    quest_df,
    x="Quest",
    y="Students Completed",
    color="Students Completed",
    color_continuous_scale="Blues",
    title="How many students completed each quest",
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ====================== INACTIVE STUDENTS ======================
st.subheader("😴 Students Inactive for 7+ Days")

if inactive:
    inactive_df = pd.DataFrame(inactive, columns=["Name", "Username", "Points", "Last Active"])
    st.dataframe(inactive_df, use_container_width=True, hide_index=True)
    st.warning(f"{len(inactive)} student(s) may need a check-in from you.")
else:
    st.success("All students have been active recently! 🎉")

st.divider()

if st.button("⬅️ Back to App"):
    st.switch_page("remote_tech_app.py")