import streamlit as st

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

import io
import sys
import contextlib
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

# ====================== PAGE CONFIG ======================
st.set_page_config(page_title="RemoteTech", page_icon="🚀", layout="wide")
init_db()

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
    db_user = st.session_state.get("db_user_name")
    if not db_user:
        return
    save_user_progress(
        db_user,
        st.session_state.points,
        st.session_state.badges,
        st.session_state.completed_lessons,
    )


BLOCKED = ["import os", "import sys", "import subprocess", "open(", "__import__"]

def safe_exec(code):
    """Run student code safely. Returns (stdout, local_vars, error)."""
    for term in BLOCKED:
        if term in code:
            return "", {}, f"'{term}' is not allowed in this exercise."
    stdout_capture = io.StringIO()
    local_vars = {}
    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(compile(code, "<student_code>", "exec"),
                 {"__builtins__": __builtins__}, local_vars)
        return stdout_capture.getvalue().strip(), local_vars, None
    except Exception as e:
        return "", {}, str(e)


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
QUESTS = [
    {"id": "1", "title": "Spaza Shop Variables",   "points": 150, "icon": "🛒"},
    {"id": "2", "title": "Taxi Fare Calculator",   "points": 150, "icon": "🚕"},
    {"id": "3", "title": "Rainy Day Decisions",    "points": 150, "icon": "🌧️"},
    {"id": "4", "title": "Spaza Restocking Loops", "points": 150, "icon": "📦"},
    {"id": "5", "title": "Super Functions",        "points": 150, "icon": "🦸"},
    {"id": "6", "title": "Super Spaza List Magic", "points": 280, "icon": "✨"},
]

# ====================== SIDEBAR ======================
st.sidebar.markdown(f"## {st.session_state.avatar} {st.session_state.user_name}")
st.sidebar.markdown("## 🎮 Menu")
page = st.sidebar.radio("Choose your adventure:", [
    "🏠 Home Base",
    "📚 Learning Quests",
    "🛒 Spaza Shop Project",
    "🧪 Magic Code Lab",
    "🏆 Hero Leaderboard",
    "📊 Village Impact",
])

st.sidebar.divider()
if st.sidebar.button("👤 My Profile", use_container_width=True):
    st.switch_page("profile.py")

if st.session_state.get("user_name") == "admin":
    if st.sidebar.button("🛡️ Admin Dashboard", use_container_width=True):
        st.switch_page("admin.py")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    persist_progress()
    st.session_state.clear()
    st.success("You have been logged out.")
    st.switch_page("login.py")
    st.stop()

# ====================== HOME ======================
if page == "🏠 Home Base":
    st.title("🚀 RemoteTech Adventure")
    st.markdown("### *Sterkspruit Heroes – Learn Python & Build Your Future!* 🌟")
    st.markdown(f"## Welcome back, *{st.session_state.full_name}*! 👋 You're a superstar! 🔥")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Points", st.session_state.points)
    with col2:
        st.metric("🏅 Badges", len(st.session_state.badges))
    with col3:
        completed = len(st.session_state.completed_lessons)
        st.metric("📚 Quests Done", f"{completed} / 6")

    if st.session_state.badges:
        st.markdown("### Your Badges")
        st.write("  ".join(st.session_state.badges))

    if len(st.session_state.completed_lessons) >= 5:
        st.success("🎓 You are close to earning your Certificate!")

    if len(st.session_state.completed_lessons) >= 6:
        if st.button("Claim Certificate 🏅", type="primary"):
            st.session_state.show_certificate = True
            st.rerun()

# ====================== LEARNING QUESTS ======================
elif page == "📚 Learning Quests":
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

    # ---- Quest 1 ----
    if active == "1":
        st.markdown("### 🛒 Quest 1: Spaza Shop Variables")
        st.write("Create variables for three items and calculate the total stock value.")
        code = st.text_area("Write your code:", height=180, key="code_1", value=
            'bread = 15\nmilk = 18\nchips = 12\ntotal = bread + milk + chips\nprint("Total: R" + str(total))')

        if st.button("Run ✨", key="run_1"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "total" not in variables:
                show_hints("1", [
                    "You need to store three numbers — what Python keyword creates a named value?",
                    "Try: bread = 15 — now do the same for milk and chips.",
                    "Add them: total = bread + milk + chips, then print('Total: R' + str(total))",
                ])
            elif not isinstance(variables.get("total"), (int, float)):
                st.warning("💡 `total` should be a number — try adding your variables together.")
            elif not output:
                st.warning("💡 Your code runs but prints nothing — add a print() statement.")
            else:
                if "1" not in st.session_state.completed_lessons:
                    record_time_and_save("1", 150)
                    st.success("🎉 Perfect! +150 points")
                    st.balloons()
                else:
                    st.info("Quest 1 already completed — great work! ✅")

    # ---- Quest 2 ----
    elif active == "2":
        st.markdown("### 🚕 Quest 2: Taxi Fare Calculator")
        st.write("Calculate taxi fare based on distance and rate per km.")
        code = st.text_area("Write your code:", height=180, key="code_2", value=
            'distance = 10\nrate = 5\nfare = distance * rate\nprint("Fare: R" + str(fare))')

        if st.button("Calculate Fare ✨", key="run_2"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "fare" not in variables:
                show_hints("2", [
                    "You need a variable called `fare` — what calculation gives you the fare?",
                    "Fare = distance × rate. Try: fare = distance * rate",
                    "Now print it: print('Fare: R' + str(fare))",
                ])
            elif variables.get("fare") != variables.get("distance", 0) * variables.get("rate", 0):
                st.warning("💡 `fare` should equal `distance × rate`. Check your formula.")
            elif str(variables.get("fare", "")) not in output:
                st.warning(f"💡 Print the fare! Got: `{output}`")
            else:
                if "2" not in st.session_state.completed_lessons:
                    record_time_and_save("2", 150)
                    st.success("🎉 Great work! +150 points")
                    st.balloons()
                else:
                    st.info("Quest 2 already completed ✅")

    # ---- Quest 3 ----
    elif active == "3":
        st.markdown("### 🌧️ Quest 3: Rainy Day Decisions")
        st.write("Use if-elif-else to decide what to do based on the weather.")
        code = st.text_area("Write your code:", height=250, key="code_3", value=
            'weather = "rainy"\nif weather == "sunny":\n    print("Go outside and play!")\nelif weather == "rainy":\n    print("Stay inside and read a book!")\nelse:\n    print("Check the weather again!")')

        if st.button("Decide ✨", key="run_3"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "weather" not in variables:
                show_hints("3", [
                    "Start by creating a variable: weather = 'rainy'",
                    "Use `if` to check one condition, `elif` for another.",
                    "if weather == 'sunny': ... elif weather == 'rainy': ... else: ...",
                ])
            elif "if" not in code or "elif" not in code:
                st.warning("💡 You need both an `if` and an `elif` block.")
            elif not output:
                st.warning("💡 Your code runs but prints nothing — add print() inside each block.")
            elif variables.get("weather") == "rainy" and "inside" not in output.lower() and "book" not in output.lower():
                st.warning(f"💡 When weather is 'rainy' suggest staying inside. Got: `{output}`")
            else:
                if "3" not in st.session_state.completed_lessons:
                    record_time_and_save("3", 150)
                    st.success("🎉 Excellent! +150 points")
                    st.balloons()
                else:
                    st.info("Quest 3 already completed ✅")

    # ---- Quest 4 ----
    elif active == "4":
        st.markdown("### 📦 Quest 4: Spaza Restocking Loops")
        st.write("Use a for loop to print a restocking message for every item.")
        code = st.text_area("Write your code:", height=180, key="code_4", value=
            'items = ["Bread", "Milk", "Chips"]\nfor item in items:\n    print("Restocking " + item)')

        if st.button("Restock ✨", key="run_4"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "items" not in variables or not isinstance(variables.get("items"), list):
                show_hints("4", [
                    "Create a list called `items` with some product names.",
                    "Use: items = ['Bread', 'Milk', 'Chips']",
                    "Then loop: for item in items:  print('Restocking ' + item)",
                ])
            elif "for" not in code:
                st.warning("💡 You need a `for` loop to go through each item.")
            elif len(output.splitlines()) < len(variables.get("items", [])):
                st.warning(f"💡 Your loop should print one line per item — got {len(output.splitlines())} line(s) for {len(variables.get('items', []))} item(s).")
            else:
                if "4" not in st.session_state.completed_lessons:
                    record_time_and_save("4", 150)
                    st.success("🎉 Well done! +150 points")
                    st.balloons()
                else:
                    st.info("Quest 4 already completed ✅")

    # ---- Quest 5 ----
    elif active == "5":
        st.markdown("### 🦸 Quest 5: Super Functions")
        st.write("Define a function called `calculate_total` that takes a list of prices and returns their sum.")
        code = st.text_area("Write your code:", height=250, key="code_5", value=
            'def calculate_total(prices):\n    total = sum(prices)\n    return total\n\nprices = [15, 18, 12]\ntotal_price = calculate_total(prices)\nprint("Total Price: R" + str(total_price))')

        if st.button("Calculate Total ✨", key="run_5"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "def " not in code:
                show_hints("5", [
                    "You need to define a function — start with `def`.",
                    "def calculate_total(prices):  — now add the body.",
                    "Inside the function: total = sum(prices)  then  return total",
                ])
            elif "calculate_total" not in variables or not callable(variables.get("calculate_total")):
                st.warning("💡 Name your function exactly `calculate_total`.")
            else:
                try:
                    result = variables["calculate_total"]([10, 20, 30])
                    if result != 60:
                        st.warning(f"💡 Your function returned `{result}` for [10, 20, 30] — expected 60. Check your sum() logic.")
                    else:
                        if "5" not in st.session_state.completed_lessons:
                            record_time_and_save("5", 150)
                            st.success("🎉 Fantastic! +150 points")
                            st.balloons()
                        else:
                            st.info("Quest 5 already completed ✅")
                except Exception as e:
                    st.error(f"❌ Your function crashed when called: {e}")

    # ---- Quest 6 ----
    elif active == "6":
        st.markdown("### ✨ Quest 6: Super Spaza List Magic")
        st.write("Use list comprehensions to raise all prices by R3, and filter prices above R20.")
        code = st.text_area("Write your code:", height=250, key="code_6", value=
            'prices = [12, 18, 25, 8, 30]\nnew_prices = [p + 3 for p in prices]\nexpensive = [p for p in prices if p > 20]\nprint(new_prices)\nprint(expensive)')

        if st.button("✨ Cast Magic!", key="run_6"):
            output, variables, error = safe_exec(code)
            if error:
                st.error(f"❌ Error: {error}")
            elif "new_prices" not in variables or "expensive" not in variables:
                show_hints("6", [
                    "You need two lists: `new_prices` and `expensive`.",
                    "Use a list comprehension: [p + 3 for p in prices]",
                    "Filter expensive ones: [p for p in prices if p > 20]",
                ])
            elif not isinstance(variables.get("new_prices"), list):
                st.warning("💡 `new_prices` should be a list — use a list comprehension.")
            elif variables.get("new_prices") != [p + 3 for p in variables.get("prices", [])]:
                st.warning(f"💡 `new_prices` should add 3 to every price. Got: `{variables.get('new_prices')}`")
            elif variables.get("expensive") != [p for p in variables.get("prices", []) if p > 20]:
                st.warning(f"💡 `expensive` should only include prices above 20. Got: `{variables.get('expensive')}`")
            else:
                if "6" not in st.session_state.completed_lessons:
                    record_time_and_save("6", 280)
                    st.success("🎉 Masterful! +280 points")
                    st.balloons()
                else:
                    st.info("Quest 6 already completed ✅")

# ====================== SPAZA SHOP PROJECT ======================
elif page == "🛒 Spaza Shop Project":
    st.header("🛒 Final Boss: Spaza Shop Management System")
    st.write("Build a complete mini system using everything you learned!")

    code = st.text_area("Build your Spaza Shop System:", height=400, value=
        '# Your Spaza Shop System\nitems = ["Bread", "Milk", "Chips", "Eggs"]\nprices = [15, 18, 12, 20]\n\ndef calculate_total(cart):\n    return sum(cart)\n\ncart = [prices[0], prices[2]]  # Bread + Chips\nprint("Items in cart:", [items[i] for i in range(len(cart))])\nprint("Total: R", calculate_total(cart))\n')

    if st.button("🚀 Launch Spaza Shop", type="primary"):
        output, variables, error = safe_exec(code)
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
        output, _, error = safe_exec(code)
        if error:
            st.error(f"Error: {error}")
        else:
            st.code(output or "(no output)", language=None)
            st.success("✅ Ran successfully!")

# ====================== LEADERBOARD ======================
elif page == "🏆 Hero Leaderboard":
    st.header("🏆 Hero Leaderboard")
    leaderboard_data = get_leaderboard()
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
if st.session_state.get("show_certificate") or len(st.session_state.completed_lessons) >= 6:
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