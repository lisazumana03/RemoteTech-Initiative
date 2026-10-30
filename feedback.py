import pandas as pd
import streamlit as st

from remotetech_data import (
    FEEDBACK_CATEGORIES,
    FEEDBACK_STATUSES,
    get_all_application_feedback,
    get_user_application_feedback,
    init_db,
    save_application_feedback,
    update_application_feedback_status,
)

init_db()

st.set_page_config(page_title="Application Feedback | RemoteTech", page_icon="💬", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please log in with a registered account to access application feedback.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("login.py")
    st.stop()

username = st.session_state.get("username", "")
role = st.session_state.get("role", "student")
is_demo = bool(st.session_state.get("is_demo", False))

APPLICATIONS = [
    "RemoteTech Learning Platform",
    "Learning Lessons",
    "Python Coding Sandbox",
    "Quests and Challenges",
    "Progress Tracking",
]

st.title("💬 Application Feedback")
st.write("Tell us what is working well, report a problem, or suggest an improvement. Your feedback helps the RemoteTech team improve the learning experience.")
st.caption("One review per application. You can submit again later to update your review.")

if is_demo or username == "demo_hero":
    st.info("Feedback submission is available only to registered users. Please register or log in with your own account.")
else:
    st.subheader("✍️ Submit or update a review")
    with st.form("application_feedback_form", clear_on_submit=False):
        application_name = st.selectbox("Application", APPLICATIONS)
        rating = st.select_slider(
            "Your rating",
            options=[1, 2, 3, 4, 5],
            value=4,
            format_func=lambda value: f"{'⭐' * value} ({value}/5)",
        )
        category = st.selectbox("Feedback category", FEEDBACK_CATEGORIES)
        review = st.text_area(
            "Your review",
            placeholder="Describe your experience, the problem you encountered, or the improvement you would like to see...",
            max_chars=2000,
            height=160,
        )
        submitted = st.form_submit_button("Submit Feedback", type="primary")

    if submitted:
        try:
            save_application_feedback(username, application_name, rating, category, review)
            st.success("Your feedback has been saved. Thank you for helping improve RemoteTech!")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("We could not save your feedback. Please try again.")

st.divider()
st.subheader("📝 My reviews")
if is_demo or username == "demo_hero":
    st.info("Personal reviews are available after you log in with a registered account.")
else:
    try:
        my_reviews = get_user_application_feedback(username)
    except Exception:
        my_reviews = []
        st.error("Your reviews could not be loaded right now.")

    if my_reviews:
        for item in my_reviews:
            with st.container(border=True):
                st.markdown(f"### {item['application_name']}")
                st.write(f"**Rating:** {'⭐' * int(item['rating'])} ({item['rating']}/5)")
                st.write(f"**Category:** {item['category']}")
                st.write(item["review"])
                st.caption(f"Status: {item['status']} · Submitted: {item['created_at']}")
    else:
        st.info("You have not submitted any reviews yet.")

# Only admins can see all users' feedback and manage its status.
if role == "admin":
    st.divider()
    st.header("🛠️ Feedback Management")
    st.caption("This section is visible to authorised administrators only.")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        app_filter = st.selectbox("Filter by application", ["All applications"] + APPLICATIONS)
    with filter_col2:
        status_filter = st.selectbox("Filter by status", ["All statuses"] + list(FEEDBACK_STATUSES))

    try:
        all_reviews = get_all_application_feedback(
            application_name=None if app_filter == "All applications" else app_filter,
            status=None if status_filter == "All statuses" else status_filter,
        )
    except Exception:
        all_reviews = []
        st.error("Feedback could not be loaded. Check the database connection.")

    if all_reviews:
        frame = pd.DataFrame(all_reviews)
        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Reviews shown", len(frame))
        metric2.metric("Average rating", f"{frame['rating'].mean():.2f}/5")
        metric3.metric("Open reviews", int((frame["status"] == "Open").sum()))
        st.dataframe(
            frame[["id", "username", "application_name", "rating", "category", "review", "status", "created_at"]],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Update review status")
        options = {
            f"#{item['id']} · {item['application_name']} · {item['username']} · {item['rating']}/5": item
            for item in all_reviews
        }
        selected_label = st.selectbox("Select a review", list(options.keys()))
        selected_item = options[selected_label]
        new_status = st.selectbox(
            "New status",
            list(FEEDBACK_STATUSES),
            index=list(FEEDBACK_STATUSES).index(selected_item["status"]),
        )
        if st.button("Save status", type="primary"):
            try:
                update_application_feedback_status(selected_item["id"], new_status)
                st.success("Review status updated.")
                st.rerun()
            except Exception:
                st.error("The review status could not be updated.")
    else:
        st.info("No reviews match these filters yet.")
