import streamlit as st

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

import pandas as pd
import plotly.express as px
from datetime import datetime
from remotetech_data import init_db, save_user_progress

st.set_page_config(page_title="RemoteTech", page_icon="🚀", layout="wide")
init_db()

# Ensure required session state keys exist before page rendering.
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'db_user_name' not in st.session_state:
    st.session_state.db_user_name = None
if 'points' not in st.session_state:
    st.session_state.points = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []
if 'completed_lessons' not in st.session_state:
    st.session_state.completed_lessons = set()
if 'show_certificate' not in st.session_state:
    st.session_state.show_certificate = False


def persist_progress():
    db_user_name = st.session_state.get('db_user_name')
    if not db_user_name:
        return

    save_user_progress(
        db_user_name,
        st.session_state.points,
        st.session_state.badges,
        st.session_state.completed_lessons,
    )

# Kid-Friendly CSS
st.markdown("""
<style>
    .main {background-color: #0f172a; color: #e0f2fe;}
    h1, h2, h3 {color: #22d3ee; font-family: 'Arial', cursive;}
    .stButton>button {background-color: #22d3ee; color: #0f172a; font-size: 18px; font-weight: bold; border-radius: 20px;}
    .hint {background-color: #334155; padding: 12px; border-radius: 12px; border-left: 5px solid #eab308;}
    .certificate {background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 40px; border-radius: 20px; text-align: center; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 RemoteTech Adventure")
st.markdown("### *Sterkspruit Heroes – Learn Python & Build Your Future!* 🌟")

st.sidebar.markdown("## 🎮 Menu")
page = st.sidebar.radio("Choose your adventure:",
                        ["🏠 Home Base", "📚 Learning Quests", "🛒 Spaza Shop Project", "🧪 Magic Code Lab",
                         "🏆 Hero Leaderboard", "📊 Village Impact"])

# ====================== HOME ======================
if page == "🏠 Home Base":
    st.markdown(f"## Welcome back, *{st.session_state.user_name}*! 👋 You're a superstar! 🔥")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⭐ Level", "6", "Next: Spaza Boss")
    with col2:
        st.metric("🔥 Points", st.session_state.points)
    with col3:
        st.metric("🏅 Badges", len(st.session_state.badges))

    if len(st.session_state.completed_lessons) >= 5:
        st.success("🎓 You are close to earning your Certificate!")
        if st.button("Claim Certificate 🏅", type="primary"):
            st.session_state.show_certificate = True
            st.rerun()

# ====================== LEARNING QUESTS (with hints & better validation) ======================
elif page == "📚 Learning Quests":
    st.header("🌟 Your Learning Quests")

    lesson_choice = st.selectbox("Choose a Quest", [
        "1. Spaza Shop Variables", "2. Taxi Fare Calculator", "3. Rainy Day Decisions",
        "4. Spaza Restocking Loops", "5. Super Functions", "6. Super Spaza List Magic"
    ])

    # Quest 1
    if lesson_choice == "1. Spaza Shop Variables":
        st.markdown("### 🛒 *Quest 1: Spaza Shop Stock*")
        st.write("Create variables and calculate total stock value.")
        code = st.text_area("Write your code:",
                            '''bread = 15\nmilk = 18\nchips = 12\ntotal = bread + milk + chips\nprint("Total: R" + str(total))''',
                            height=180)
        if st.button("Run ✨", key="q1"):
            if "total" in code and "print" in code:
                try:
                    exec(code)
                    if "1" in st.session_state.completed_lessons:
                        st.info("Quest 1 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 150
                        st.session_state.completed_lessons.add("1")
                        persist_progress()
                        st.success("🎉 Perfect! +150 points")
                        st.balloons()
                except:
                    st.error("Almost! Check your code.")
            else:
                st.warning("Hint: Create variables then calculate total and print it.")

    # Quest 2
    if lesson_choice == "2. Taxi Fare Calculator":
        st.markdown("### 🚕 *Quest 2: Taxi Fare Calculator*")
        st.write("Calculate taxi fare based on distance and rate.")
        code = st.text_area("Write your code:",
                            '''distance = 10\nrate = 5\nfare = distance * rate\nprint("Fare: R" + str(fare))''', height=180)
        if st.button("Calculate Fare ✨", key="q2"):
            if "fare" in code and "print" in code:
                try:
                    exec(code)
                    if "2" in st.session_state.completed_lessons:
                        st.info("Quest 2 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 150
                        st.session_state.completed_lessons.add("2")
                        persist_progress()
                        st.success("🎉 Great! +150 points")
                        st.balloons()
                except:
                    st.error("Check your calculations!")
            else:
                st.warning("Hint: Calculate fare using distance and rate, then print it.")

    # Quest 3 (Grading system according to the South African school system)
    if lesson_choice == "3. Rainy Day Decisions":
        st.markdown("### 🌧️ *Quest 3: Rainy Day Decisions*")
        st.write("Use if-else to decide what to do on a rainy day.")
        code = st.text_area("Write your code:",
                            '''weather = "rainy"\nif weather == "sunny":\n    print("Go outside and play!")\nelif weather == "rainy":\n    print("Stay inside and read a book!")\nelse:\n    print("Check the weather again!")''',
                            height=250)
        if st.button("Decide ✨", key="q3"):
            if "if weather" in code and "elif weather" in code:
                try:
                    exec(code)
                    if "3" in st.session_state.completed_lessons:
                        st.info("Quest 3 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 150
                        st.session_state.completed_lessons.add("3")
                        persist_progress()
                        st.success("🎉 Excellent! +150 points")
                        st.balloons()
                except:
                    st.error("Check your conditions!")
            else:
                st.warning("Hint: Use if-elif to check the weather and print decisions.")
    
    #Quest 4
    if lesson_choice == "4. Spaza Restocking Loops":
        st.markdown("### 📦 *Quest 4: Spaza Restocking Loops*")
        st.write("Use a for loop to restock items.")
        code = st.text_area("Write your code:",
                            '''items = ["Bread", "Milk", "Chips"]\nfor item in items:\n    print("Restocking " + item)''', height=180)
        if st.button("Restock ✨", key="q4"):
            if "for item in items" in code and "print" in code:
                try:
                    exec(code)
                    if "4" in st.session_state.completed_lessons:
                        st.info("Quest 4 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 150
                        st.session_state.completed_lessons.add("4")
                        persist_progress()
                        st.success("🎉 Well done! +150 points")
                        st.balloons()
                except:
                    st.error("Check your loop syntax!")
            else:
                st.warning("Hint: Use a for loop to go through items and print restocking messages.")
    
    # Quest 5
    if lesson_choice == "5. Super Functions":
        st.markdown("### 🦸 *Quest 5: Super Functions*")
        st.write("Create a function to calculate total price.")
        code = st.text_area("Write your code:",
                            '''def calculate_total(prices):\n    total = sum(prices)\n    return total\n\nprices = [15, 18, 12]\ntotal_price = calculate_total(prices)\nprint("Total Price: R" + str(total_price))''', height=250)
        if st.button("Calculate Total ✨", key="q5"):
            if "def calculate_total" in code and "return total" in code:
                try:
                    exec(code)
                    if "5" in st.session_state.completed_lessons:
                        st.info("Quest 5 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 150
                        st.session_state.completed_lessons.add("5")
                        persist_progress()
                        st.success("🎉 Fantastic! +150 points")
                        st.balloons()
                except:
                    st.error("Check your function definition and return statement!")
            else:
                st.warning("Hint: Define a function that takes prices, calculates total using sum(), and returns it.")
    # Quest 6
    elif lesson_choice == "6. Super Spaza List Magic":
        st.markdown("### ✨ *Quest 6: Super Spaza List Magic*")
        st.write("Use list comprehensions to update prices.")
        code = st.text_area("Write your list comprehensions:",
                            '''prices = [12, 18, 25, 8, 30]\nnew_prices = [p + 3 for p in prices]\nexpensive = [p for p in prices if p > 20]\nprint(new_prices)\nprint(expensive)''', height=250)
        if st.button("✨ Cast Magic!", key="q6"):
            if "for p in prices" in code and "if p >" in code:
                try:
                    exec(code)
                    if "6" in st.session_state.completed_lessons:
                        st.info("Quest 6 is already completed. Your progress has been saved.")
                    else:
                        st.session_state.points += 280
                        st.session_state.completed_lessons.add("6")
                        persist_progress()
                        st.success("🎉 Masterful! +280 points")
                        st.balloons()
                except:
                    st.error("Small error")
            else:
                st.info("*Hint:* Use [p + 3 for p in prices] and [p for p in prices if p > 20]")
    
    # ... (I kept quests 2-5 similar to previous version with hints added)

# ====================== NEW MINI PROJECT ======================
elif page == "🛒 Spaza Shop Project":
    st.header("🛒 *Final Boss: Spaza Shop Management System*")
    st.write("Build a complete mini system using everything you learned!")

    code = st.text_area("Build your Spaza Shop System:", height=400, value='''# Your Spaza Shop System
items = ["Bread", "Milk", "Chips", "Eggs"]
prices = [15, 18, 12, 20]

def calculate_total(cart):
    return sum(cart)

# Example usage
cart = [prices[0], prices[2]]  # Bread + Chips
print("Items in cart:", [items[i] for i in range(len(cart))])
print("Total: R", calculate_total(cart))
''')

    if st.button("🚀 Launch Spaza Shop", type="primary"):
        try:
            exec(code)
            if "🛒 Spaza Tycoon" in st.session_state.badges:
                st.info("Spaza Tycoon badge is already saved on your profile.")
            else:
                st.session_state.points += 500
                st.session_state.badges.append("🛒 Spaza Tycoon")
                persist_progress()
                st.success("🎉 *Congratulations!* You built a full Spaza Shop System!")
                st.balloons()
                st.success("You are now ready for real-world coding!")
        except Exception as e:
            st.error(f"Fix this: {e}")

# ====================== CERTIFICATE ======================
if getattr(st.session_state, 'show_certificate', False) or len(st.session_state.completed_lessons) >= 6:
    st.markdown('<div class="certificate">', unsafe_allow_html=True)
    st.markdown("# 🎓 Certificate of Completion")
    st.markdown("### RemoteTech Python Mastery Program")
    st.markdown(f"*This certifies that*")
    st.markdown(st.session_state.user_name)
    st.markdown("*has successfully completed the Sterkspruit Python Coding Adventure*")
    st.markdown(f"*Date:* {datetime.now().strftime('%d %B %Y')}")
    st.markdown(f"*Total Points:* {st.session_state.points} 🔥")
    st.markdown("*Well done, Future Tech Leader!* 🌍")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Download Certificate (Screenshot this)"):
        st.success("Certificate ready! Take a screenshot 🎉")

# ====================== Other Pages (Magic Lab, Leaderboard, Impact) ======================
elif page == "🧪 Magic Code Lab":
    st.header("🧪 Free Magic Code Lab")
    code = st.text_area("Experiment freely:", height=350)
    if st.button("Run Code ✨"):
        try:
            exec(code)
            st.success("✅ Worked!")
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

# Leaderboard & Impact pages remain similar...

# Leaderboard to be presented in a form of a table with points and badges
elif page == "🏆 Hero Leaderboard":
    st.header("🏆 Hero Leaderboard")
    leaderboard_data = {
        "Position": [1, 2, 3, 4],
        "Hero": ["Akhona M.", "Sipho D.", "Lerato K.", "Thabo N."],
        "Points": [850, 720, 680, 600],
        "Badges": ["🔥 First Spell, 🛒 Spaza Boss", "🔥 First Spell", "🛒 Spaza Boss", ""]
    }
    leaderboard_df = pd.DataFrame(leaderboard_data)
    st.table(leaderboard_df)

elif page == "📊 Village Impact":
    st.header("📊 Village Impact")
    st.markdown("### 🌍 *Coding Impact in Sterkspruit*")
    impact_data = {
        "Category": ["Education", "Employment", "Community Projects", "Tech Awareness"],
        "Impact Score": [85, 70, 60, 90]
    }
    impact_df = pd.DataFrame(impact_data)
    fig = px.pie(impact_df, names="Category", values="Impact Score", title="Coding Impact Distribution")
    st.plotly_chart(fig)

st.sidebar.title("🚀 RemoteTech")

if st.sidebar.button("🚪 Logout", use_container_width=True):

    # Save progress first
    persist_progress()

    # Clear all session data
    st.session_state.clear()

    st.success("You have been logged out.")

    st.switch_page("login.py")
    st.stop()

st.caption("RemoteTech ©️ 2026 • Sterkspruit Pilot • Eastern Cape")