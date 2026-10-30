import streamlit as st
import os

from remotetech_data import init_db, register_user, create_email_verification_token, EMAIL_VERIFICATION_TTL_HOURS
from email_utils import send_email, is_configured
import billing

init_db()
billing.init_billing_tables()

st.set_page_config(page_title="RemoteTech — Register a School", page_icon="🏫")
st.title("🏫 Register as a Teacher / Admin")
st.caption("Requires a license key from your school's purchase — see the Pricing page if you don't have one yet.")

license_key = st.text_input("License Key", help="Looks like XXXX-XXXX-XXXX-XXXX, shown once after checkout.")
full_name = st.text_input("Full Name")
username = st.text_input("Username")
email = st.text_input("Email")
class_name = st.text_input("Default Class Code (optional)", help="Students in this class will show up on your dashboard by default.")
password = st.text_input("Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")

if st.button("Register", type="primary"):
    license_record = billing.validate_license_key(license_key) if license_key else None

    if not license_key:
        st.error("Please enter your license key.")
    elif not license_record:
        st.error("That license key isn't valid, is inactive, or has no seats left. Check the key or contact us.")
    elif not full_name or not username or not email or not password:
        st.error("Please fill in all fields.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters.")
    else:
        success = register_user(
            full_name=full_name,
            username=username,
            email=email,
            password=password,
            avatar="🧑‍🏫",
            role="admin",
            popia_consent=True,
            school=license_record["school_name"],
            class_name=class_name.strip(),
            email_verified=False,
        )
        if success:
            billing.redeem_seat(license_record["id"])
            token = create_email_verification_token(username.strip(), email.strip())
            base_url = os.environ.get("APP_BASE_URL", "").rstrip("/")
            verify_link = f"{base_url}/verify_email?token={token}" if base_url and token else ""
            sent = bool(token and verify_link and is_configured() and send_email(
                email.strip(), "Verify your RemoteTech school administrator email",
                f"Hi {full_name},\n\nVerify your email to activate your RemoteTech school administrator account.\n\n"
                f"Open this link within {EMAIL_VERIFICATION_TTL_HOURS} hours:\n{verify_link}\n\n"
                "If you did not create this account, ignore this email."
            ))
            st.success(f"Account created for {license_record['school_name']}. Verify your email before logging in.")
            if not sent:
                st.warning("Verification email could not be sent. Please contact the application administrator. The verification link is not displayed here.")
        else:
            st.error("That username or email is already registered.")

st.divider()
if st.button("👉 Go to Login"):
    st.switch_page("login.py")
