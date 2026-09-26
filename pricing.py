import streamlit as st

import billing

billing.init_billing_tables()

st.set_page_config(page_title="RemoteTech — Pricing", page_icon="💳")
st.title("💳 Bring RemoteTech to Your School")
st.caption("Pick a plan, pay securely via Stripe, and get a license key your teachers use to set up their accounts.")

cols = st.columns(len(billing.PLANS))
for col, (plan_key, plan) in zip(cols, billing.PLANS.items()):
    with col:
        st.subheader(plan["label"])
        st.markdown(f"### {plan['price_display']}")
        st.caption(f"Up to {plan['seats']} teacher/admin accounts")

st.divider()

st.subheader("Purchase a License")
plan_choice = st.selectbox(
    "Plan",
    options=list(billing.PLANS.keys()),
    format_func=lambda k: f"{billing.PLANS[k]['label']} — {billing.PLANS[k]['price_display']}",
)
school_name = st.text_input("School name")
contact_email = st.text_input("Contact email (for the receipt and license key)")

if billing.stripe_configured():
    if st.button("Pay with Card →", type="primary"):
        if not school_name or not contact_email:
            st.error("Please fill in your school name and contact email.")
        else:
            try:
                # Streamlit apps are typically served behind a fixed base URL in
                # production; set APP_BASE_URL so the Stripe redirect lands back here.
                import os
                base_url = os.environ.get("APP_BASE_URL", "http://localhost:8501").rstrip("/")
                checkout_url = billing.create_checkout_session(
                    plan_key=plan_choice,
                    school_name=school_name,
                    contact_email=contact_email,
                    success_url=f"{base_url}/activate",
                    cancel_url=f"{base_url}/pricing",
                )
                st.link_button("Continue to Secure Checkout →", checkout_url, type="primary")
            except Exception as e:
                st.error(f"Couldn't start checkout: {e}")
else:
    st.info(
        "Card payments aren't switched on yet in this environment. "
        "Submit your details and we'll follow up to invoice you directly — "
        "you'll still get a license key once payment is confirmed."
    )
    if st.button("Request an Invoice"):
        if not school_name or not contact_email:
            st.error("Please fill in your school name and contact email.")
        else:
            st.success(
                f"Thanks! We'll email {contact_email} an invoice for the "
                f"{billing.PLANS[plan_choice]['label']} plan for {school_name}."
            )

st.divider()
st.caption("Already have a license key? Go to **Register a School** to set up your teacher/admin account.")
if st.button("👉 Register a School"):
    st.switch_page("register_school.py")
