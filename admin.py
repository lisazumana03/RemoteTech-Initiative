import json

import streamlit as st
import pandas as pd
import plotly.express as px
from remotetech_data import (
    init_db,
    get_all_student_progress,
    get_inactive_students,
    get_quest_completion_stats,
    get_all_classes,
)
import quests_store
import billing
from branding import get_branding, save_branding

init_db()
quests_store.init_quests_table()
billing.init_billing_tables()

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

# NOTE: this used to check `user_name != "admin"`, which only ever matched
# a hardcoded username. It now checks the actual `role` set at login/seed
# time (see seed_admin.py), which is what main.py's navigation menu uses
# to decide whether to show this page in the first place.
if st.session_state.get("role") != "admin":
    st.error("⛔ You do not have permission to view this page.")
    st.stop()

st.set_page_config(page_title="Admin Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Teacher / Admin Dashboard")
st.caption("RemoteTech Sterkspruit Pilot — Class Overview")

st.subheader("🎨 School Branding")
st.caption("These settings apply to your school's learner pages and shared progress links.")
current_branding = get_branding(st.session_state.get("school", ""))
brand_col1, brand_col2 = st.columns(2)
with brand_col1:
    logo_url = st.text_input("Logo URL (optional)", value=current_branding["logo_url"])
    primary_color = st.color_picker("Primary color", current_branding["primary_color"])
with brand_col2:
    accent_color = st.color_picker("Accent color", current_branding["accent_color"])
    language = st.selectbox("Default language", ["en", "xh", "af"], index=["en", "xh", "af"].index(current_branding["language"]))
if st.button("Save Branding", type="primary"):
    if not st.session_state.get("school"):
        st.error("Your admin account is not linked to a school.")
    else:
        save_branding(st.session_state.school, logo_url, primary_color, accent_color, language)
        st.success("Branding saved. Learners will see it on their next page load.")

st.divider()

# ====================== CLASS SCOPE ======================
# Admins/teachers only see their own class by default (matching the class
# code on their own account, set at registration or on their Profile page),
# but can switch to any other class, or "All Classes", from the dropdown.
all_classes = get_all_classes()
own_class = st.session_state.get("class_name") or None
class_options = ["All Classes"] + all_classes
default_index = class_options.index(own_class) if own_class in class_options else 0

selected_class = st.selectbox("🏫 Class", class_options, index=default_index)
scope = None if selected_class == "All Classes" else selected_class

ALL_QUESTS = quests_store.get_all_quests()
CORE_QUEST_IDS = [q["id"] for q in ALL_QUESTS if q.get("quest_set") == "foundations"]

students    = get_all_student_progress(class_name=scope)
quest_stats = get_quest_completion_stats(class_name=scope, quest_ids=[q["id"] for q in ALL_QUESTS])
inactive    = get_inactive_students(days=7, class_name=scope)

# ====================== TOP METRICS ======================
total_students  = len(students)
completed_all   = sum(1 for s in students if s["lessons_count"] >= len(CORE_QUEST_IDS))
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
        row = {
            "Name":         s["full_name"],
            "Username":     s["user_name"],
            "Points":       s["points"],
            "Quests Done":  f"{s['lessons_count']} / {len(ALL_QUESTS)}",
            "Badges":       ", ".join(s["badges"]) if s["badges"] else "None",
            "Last Active":  s.get("last_active") or "Never",
            "Status":       "✅ Complete"   if s["lessons_count"] >= len(CORE_QUEST_IDS)
                            else ("⚠️ In Progress" if s["lessons_count"] > 0
                            else "🔴 Not Started"),
        }
        if scope is None:
            # Only show the Class column when viewing multiple classes at once.
            row["Class"] = s.get("class_name") or "Unassigned"
        rows.append(row)

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

QUEST_LABELS = {q["id"]: f"Quest {q['id']}: {q['title']}" for q in ALL_QUESTS}

quest_df = pd.DataFrame([
    {"Quest": QUEST_LABELS.get(k, f"Quest {k}"), "Students Completed": v}
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

# ====================== QUEST EDITOR ======================
# Quest content now lives in the database (see quests_store.py), so it can
# be added or tweaked here — no code change, no redeploy. Each quest is
# edited as raw JSON: the same shape as one entry in quests_seed.json.
# Grading logic (the "checks" list) is documented in quest_engine.py.
st.subheader("🧩 Quest Editor")
st.caption(
    "Add or edit quest content and grading rules. Each quest is a JSON object — "
    "see quest_engine.py for the list of supported `checks` types."
)

quest_ids = ["➕ New quest..."] + [f"{q['id']} — {q['title']}" for q in ALL_QUESTS]
picked = st.selectbox("Choose a quest to edit", quest_ids)

if picked == "➕ New quest...":
    template = {
        "id": "new-quest-id",
        "sort_order": 999,
        "quest_set": "foundations",
        "icon": "🌟",
        "title": "New Quest Title",
        "description": "What the student needs to do.",
        "points": 150,
        "run_button_label": "Run ✨",
        "starter_code": "# starter code here",
        "success_message": "🎉 Well done!",
        "checks": [
            {"type": "has_var", "var": "some_var", "hints": ["hint 1", "hint 2", "hint 3"]}
        ],
    }
    editor_key = "quest_editor_new"
else:
    quest_id = picked.split(" — ")[0]
    template = quests_store.get_quest(quest_id)
    editor_key = f"quest_editor_{quest_id}"

raw_json = st.text_area(
    "Quest JSON", value=json.dumps(template, indent=2, ensure_ascii=False),
    height=340, key=editor_key,
)

col_save, col_delete = st.columns([1, 1])
with col_save:
    if st.button("💾 Save Quest", type="primary"):
        try:
            quest_dict = json.loads(raw_json)
            if not quest_dict.get("id"):
                st.error("The quest needs an `id`.")
            else:
                quests_store.save_quest(quest_dict)
                st.success(f"Saved quest '{quest_dict['id']}'. Reload this page to see it in the list above.")
        except json.JSONDecodeError as e:
            st.error(f"That's not valid JSON: {e}")
with col_delete:
    if picked != "➕ New quest..." and st.button("🗑️ Delete Quest"):
        quests_store.delete_quest(quest_id)
        st.success(f"Deleted quest '{quest_id}'. Reload this page to refresh the list.")

st.divider()

# ====================== SCHOOL LICENSES ======================
st.subheader("🏫 School Licenses")
st.caption("Licenses purchased via the Pricing page. A license key lets a teacher self-register an admin account for their school.")

licenses = billing.list_licenses()
if licenses:
    lic_df = pd.DataFrame([
        {
            "School": l["school_name"],
            "Plan": l["plan"],
            "Seats used": f"{l['redeemed_count']} / {l['seats']}",
            "Status": l["status"],
            "Created": l["created_at"],
        }
        for l in licenses
    ])
    st.dataframe(lic_df, use_container_width=True, hide_index=True)
else:
    st.info("No licenses purchased yet.")

st.divider()

if st.button("⬅️ Back to App"):
    st.switch_page("remote_tech_app.py")