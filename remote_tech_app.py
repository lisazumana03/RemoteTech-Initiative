import streamlit as st

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

import io
import sys
import time
import pandas as pd
import plotly.express as px
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from remotetech_data import (
    init_db,
    save_user_progress,
    save_quest_time,
    get_leaderboard,
)
from branding import apply_branding, get_branding, text
from sandbox import safe_exec
import quests_store
import quest_engine

# ====================== RUN-BUTTON RATE LIMITING ======================
# Per-session throttle on top of sandbox.py's process-wide concurrency cap:
# a short cooldown between runs (stops rapid-fire clicking) plus a cap on
# runs per rolling minute (stops one session from hogging the sandbox even
# at a slow-but-steady pace). This is deliberately generous — it's abuse
# protection, not a puzzle for students to work around.
RATE_LIMIT_COOLDOWN_SECONDS = 2
RATE_LIMIT_MAX_RUNS_PER_WINDOW = 10
RATE_LIMIT_WINDOW_SECONDS = 60


def _check_run_rate_limit():
    """Returns (allowed: bool, message: str | None)."""
    now = time.time()
    timestamps = st.session_state.setdefault("run_timestamps", [])
    timestamps[:] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]

    if timestamps and (now - timestamps[-1]) < RATE_LIMIT_COOLDOWN_SECONDS:
        wait = RATE_LIMIT_COOLDOWN_SECONDS - (now - timestamps[-1])
        return False, f"⏳ Please wait {wait:.1f}s before running your code again."

    if len(timestamps) >= RATE_LIMIT_MAX_RUNS_PER_WINDOW:
        return False, (
            f"⏳ You've hit the limit of {RATE_LIMIT_MAX_RUNS_PER_WINDOW} runs per minute. "
            "Take a breather and try again shortly."
        )

    timestamps.append(now)
    return True, None


def run_student_code(code, timeout=3):
    """Rate-limited wrapper around sandbox.safe_exec — use this everywhere
    the app runs student-submitted code, instead of calling safe_exec directly."""
    allowed, message = _check_run_rate_limit()
    if not allowed:
        return "", {}, message
    return safe_exec(code, timeout=timeout)

# ====================== PAGE CONFIG ======================
st.set_page_config(page_title="RemoteTech", page_icon="🚀", layout="wide")
init_db()
quests_store.init_quests_table()
branding = get_branding(st.session_state.get("school", ""))
apply_branding(branding)

# ====================== SESSION STATE DEFAULTS ======================
defaults = {
    "authenticated": False,
    "user_name": "",
    "full_name": "",
    "db_user_name": None,
    "avatar": "🚀",
    "points": 0,
    "badges": [],
    "completed_lessons": set(),
    "show_certificate": False,
    "active_quest": None,
    "quest_start_time": None,
    "school": "",
    "class_name": "",
    "is_demo": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ====================== CSS ======================
st.markdown("""
<style>
    .main {background-color: #0f172a; color: #e0f2fe;}
    h1, h2, h3 {color: #22d3ee; font-family: 'Arial', cursive;}
    .stButton>button {background-color: #22d3ee; color: #0f172a; font-size: 18px;
                      font-weight: bold; border-radius: 20px;}
    .hint {background-color: #334155; padding: 12px; border-radius: 12px;
           border-left: 5px solid #eab308;}
    .certificate {background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                  padding: 40px; border-radius: 20px; text-align: center; color: white;}
</style>
""", unsafe_allow_html=True)

# ====================== HELPERS ======================
def persist_progress():
    # Demo/trial sessions never write back to the database — the demo
    # account is shared by every visitor, so saving would let one
    # visitor's demo progress leak into another's session.
    if st.session_state.get("is_demo"):
        return
    db_user = st.session_state.get("db_user_name")
    if not db_user:
        return
    save_user_progress(
        db_user,
        st.session_state.points,
        st.session_state.badges,
        st.session_state.completed_lessons,
    )


def show_hints(quest_id, hints):
    """Show escalating hints — vague first, specific later."""
    hint_key = f"hint_level_{quest_id}"
    if hint_key not in st.session_state:
        st.session_state[hint_key] = 0
    level = min(st.session_state[hint_key], len(hints) - 1)
    st.warning(f"💡 Hint {level + 1} of {len(hints)}: {hints[level]}")
    if level < len(hints) - 1:
        if st.button("🤔 Still stuck? Get a better hint", key=f"hint_btn_{quest_id}_{level}"):
            st.session_state[hint_key] += 1
            st.rerun()


def record_time_and_save(quest_id, points_to_add, badge=None):
    """Award points, record quest time, persist — call on first completion only."""
    start = st.session_state.get("quest_start_time") or datetime.now()
    seconds = int((datetime.now() - start).total_seconds())
    st.session_state.points += points_to_add
    st.session_state.completed_lessons.add(quest_id)
    if badge and badge not in st.session_state.badges:
        st.session_state.badges.append(badge)
    if not st.session_state.get("is_demo"):
        save_quest_time(st.session_state.get("db_user_name", ""), quest_id, seconds)
    persist_progress()


def generate_certificate_pdf(user_name, points, date_str):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setFillColor(HexColor("#1e3a8a"))
    c.rect(0, 0, width, height, fill=1)
    c.setStrokeColor(HexColor("#22d3ee"))
    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60)
    c.setFillColor(HexColor("#e0f2fe"))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2, height - 120, "Certificate of Completion")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 170, "RemoteTech Python Mastery Program")
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(width / 2, height - 220, "This certifies that")
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 260, user_name)
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(width / 2, height - 300,
                        "has successfully completed the Sterkspruit Python Coding Adventure")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 340,
                        f"Date: {date_str}    |    Total Points: {points}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# ====================== QUEST DEFINITIONS ======================
# Loaded from the database (seeded from quests_seed.json the first time the
# app runs) instead of hardcoded here — an admin can add, edit or reorder
# quests from the Admin Dashboard with no code change or redeploy. See
# quests_store.py and quest_engine.py.
QUESTS = quests_store.get_all_quests()
QUESTS_BY_ID = {q["id"]: q for q in QUESTS}

# The original "core curriculum" — completing these earns the certificate.
# Extra quest sets (dictionaries, mini-projects, ...) are bonus content and
# don't block certification, so adding more content never moves the goalposts
# for a student who's already close to finishing.
CORE_QUEST_SET = "foundations"
CORE_QUEST_IDS = [q["id"] for q in QUESTS if q.get("quest_set", CORE_QUEST_SET) == CORE_QUEST_SET]

# ====================== SIDEBAR ======================
st.sidebar.markdown(f"## {st.session_state.avatar} {st.session_state.user_name}")
st.sidebar.caption(branding["school_name"])
language_options = {"English": "en", "isiXhosa": "xh", "Afrikaans": "af"}
selected_language = st.sidebar.selectbox(
    text("language"), list(language_options),
    index=list(language_options.values()).index(st.session_state.get("language", "en")),
)
if language_options[selected_language] != st.session_state.get("language", "en"):
    st.session_state.language = language_options[selected_language]
    st.rerun()
st.sidebar.markdown("## 🎮 Menu")
page = st.sidebar.radio("Choose your adventure:", [
    f"🏠 {text('home')}",
    f"📚 {text('quests')}",
    "🛒 Spaza Shop Project",
    "🧪 Magic Code Lab",
    f"🏆 {text('leaderboard')}",
    "📊 Village Impact",
])

st.sidebar.divider()
if st.sidebar.button("👤 My Profile", use_container_width=True):
    st.switch_page("profile.py")

if st.session_state.get("role") == "admin":
    if st.sidebar.button("🛡️ Admin Dashboard", use_container_width=True):
        st.switch_page("admin.py")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    persist_progress()
    st.session_state.clear()
    st.success("You have been logged out.")
    st.switch_page("login.py")
    st.stop()

if st.session_state.get("is_demo"):
    st.info(
        "🎮 **You're in Demo Mode.** Feel free to explore — nothing you do here is saved. "
        "Ready to keep your progress for real? Head to the Register page to create your own account.",
        icon="🎮",
    )

# ====================== HOME ======================
if page == f"🏠 {text('home')}":
    st.title(f"🚀 {branding['school_name']} Adventure")
    st.markdown("### *Sterkspruit Heroes – Learn Python & Build Your Future!* 🌟")
    st.markdown(f"## Welcome back, *{st.session_state.full_name}*! 👋 You're a superstar! 🔥")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Points", st.session_state.points)
    with col2:
        st.metric("🏅 Badges", len(st.session_state.badges))
    with col3:
        completed = len(st.session_state.completed_lessons)
        st.metric("📚 Quests Done", f"{completed} / {len(QUESTS)}")

    if st.session_state.badges:
        st.markdown("### Your Badges")
        st.write("  ".join(st.session_state.badges))

    core_done = sum(1 for qid in CORE_QUEST_IDS if qid in st.session_state.completed_lessons)
    if core_done >= len(CORE_QUEST_IDS) - 1 and core_done < len(CORE_QUEST_IDS):
        st.success("🎓 You are close to earning your Certificate!")

    if core_done >= len(CORE_QUEST_IDS):
        if st.button("Claim Certificate 🏅", type="primary"):
            st.session_state.show_certificate = True
            st.rerun()

# ====================== LEARNING QUESTS ======================
elif page == f"📚 {text('quests')}":
    st.header("🌟 Your Learning Quests")

    # Quest selection grid
    cols = st.columns(3)
    for i, quest in enumerate(QUESTS):
        completed = quest["id"] in st.session_state.completed_lessons
        unlocked  = quest["id"] == "1" or str(int(quest["id"]) - 1) in st.session_state.completed_lessons

        with cols[i % 3]:
            if completed:
                st.success(f"{quest['icon']} Quest {quest['id']}: {quest['title']}\n\n✅ Done! +{quest['points']} pts")
            elif unlocked:
                if st.button(f"{quest['icon']} Quest {quest['id']}: {quest['title']}\n\n▶️ Start", key=f"sel_{quest['id']}"):
                    st.session_state.active_quest = quest["id"]
                    st.session_state.quest_start_time = datetime.now()
                    # Reset hint level when starting fresh
                    st.session_state[f"hint_level_{quest['id']}"] = 0
                    st.rerun()
            else:
                st.info(f"🔒 Quest {quest['id']}: {quest['title']}\n\nComplete Quest {int(quest['id'])-1} first.")

    active = st.session_state.get("active_quest")
    if not active:
        st.stop()

    st.divider()

    quest = QUESTS_BY_ID.get(active)
    if quest is None:
        st.error("This quest is no longer available.")
        st.stop()

    st.markdown(f"### {quest['icon']} Quest {quest['id']}: {quest['title']}")
    st.write(quest["description"])
    code = st.text_area(
        "Write your code:",
        height=quest.get("editor_height", 200),
        key=f"code_{quest['id']}",
        value=quest["starter_code"],
    )

    if st.button(quest.get("run_button_label", "Run ✨"), key=f"run_{quest['id']}"):
        output, variables, error = run_student_code(code)
        if error:
            st.error(f"❌ Error: {error}")
        else:
            result = quest_engine.evaluate_quest(quest, code, output, variables)
            if result["passed"]:
                if quest["id"] not in st.session_state.completed_lessons:
                    record_time_and_save(quest["id"], quest["points"], quest.get("badge"))
                    st.success(quest.get("success_message", f"🎉 Well done! +{quest['points']} points"))
                    st.balloons()
                else:
                    st.info(f"Quest {quest['id']} already completed — great work! ✅")
            elif result.get("hints"):
                show_hints(quest["id"], result["hints"])
            else:
                st.warning(result.get("message", "💡 Not quite — check your code and try again."))

    st.stop()

# ====================== SPAZA SHOP PROJECT ======================
elif page == "🛒 Spaza Shop Project":
    st.header("🛒 Final Boss: Spaza Shop Management System")
    st.write("Build a complete mini system using everything you learned!")

    code = st.text_area("Build your Spaza Shop System:", height=400, value=
        '# Your Spaza Shop System\nitems = ["Bread", "Milk", "Chips", "Eggs"]\nprices = [15, 18, 12, 20]\n\ndef calculate_total(cart):\n    return sum(cart)\n\ncart = [prices[0], prices[2]]  # Bread + Chips\nprint("Items in cart:", [items[i] for i in range(len(cart))])\nprint("Total: R", calculate_total(cart))\n')

    if st.button("🚀 Launch Spaza Shop", type="primary"):
        output, variables, error = run_student_code(code)
        if error:
            st.error(f"Fix this: {error}")
        else:
            st.code(output, language=None)
            if "🛒 Spaza Tycoon" not in st.session_state.badges:
                st.session_state.points += 500
                st.session_state.badges.append("🛒 Spaza Tycoon")
                persist_progress()
                st.success("🎉 Congratulations! You built a full Spaza Shop System! +500 points")
                st.success("Badge earned: 🛒 Spaza Tycoon")
                st.balloons()
            else:
                st.info("Spaza Tycoon badge already earned ✅")

# ====================== MAGIC CODE LAB ======================
elif page == "🧪 Magic Code Lab":
    st.header("🧪 Free Magic Code Lab")
    st.write("Experiment freely — no grading here!")
    code = st.text_area("Write anything:", height=350)
    if st.button("Run Code ✨"):
        output, _, error = run_student_code(code)
        if error:
            st.error(f"Error: {error}")
        else:
            st.code(output or "(no output)", language=None)
            st.success("✅ Ran successfully!")

# ====================== LEADERBOARD ======================
elif page == f"🏆 {text('leaderboard')}":
    st.header("🏆 Hero Leaderboard")
    user_class = st.session_state.get("class_name")
    if user_class:
        st.caption(f"Showing your class: **{user_class}**")
    else:
        st.caption("You're not assigned to a class yet, so this shows everyone.")
    leaderboard_data = get_leaderboard(class_name=user_class)
    if leaderboard_data:
        df = pd.DataFrame(leaderboard_data)
        df.insert(0, "Position", range(1, len(df) + 1))
        st.table(df)
    else:
        st.info("No heroes on the board yet — complete quests to appear here! 🚀")

# ====================== VILLAGE IMPACT ======================
elif page == "📊 Village Impact":
    st.header("📊 Village Impact")
    st.markdown("### 🌍 Coding Impact in Sterkspruit")
    impact_data = {
        "Category": ["Education", "Employment", "Community Projects", "Tech Awareness"],
        "Impact Score": [85, 70, 60, 90],
    }
    impact_df = pd.DataFrame(impact_data)
    fig = px.pie(impact_df, names="Category", values="Impact Score",
                 title="Coding Impact Distribution")
    st.plotly_chart(fig)

# ====================== CERTIFICATE ======================
core_done_count = sum(1 for qid in CORE_QUEST_IDS if qid in st.session_state.completed_lessons)
if st.session_state.get("show_certificate") or core_done_count >= len(CORE_QUEST_IDS):
    st.divider()
    st.markdown('<div class="certificate">', unsafe_allow_html=True)
    st.markdown("# 🎓 Certificate of Completion")
    st.markdown("### RemoteTech Python Mastery Program")
    st.markdown("*This certifies that*")
    st.markdown(f"## {st.session_state.full_name}")
    st.markdown("*has successfully completed the Sterkspruit Python Coding Adventure*")
    st.markdown(f"**Date:** {datetime.now().strftime('%d %B %Y')}")
    st.markdown(f"**Total Points:** {st.session_state.points} 🔥")
    st.markdown("*Well done, Future Tech Leader!* 🌍")
    st.markdown("</div>", unsafe_allow_html=True)

    pdf_buffer = generate_certificate_pdf(
        st.session_state.full_name,
        st.session_state.points,
        datetime.now().strftime("%d %B %Y"),
    )
    st.download_button(
        label="📄 Download Certificate (PDF)",
        data=pdf_buffer,
        file_name=f"RemoteTech_Certificate_{st.session_state.user_name}.pdf",
        mime="application/pdf",
    )

st.caption("RemoteTech ©️ 2026 • Sterkspruit Pilot • Eastern Cape")