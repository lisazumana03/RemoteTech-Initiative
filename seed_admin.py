"""
seed_admin.py — One-off local script to create an admin account.

This is NOT part of the Streamlit app and is never imported by it.
Run it directly from your terminal, once, to create a teacher/admin login.
It talks to the same remotetech.db file the app uses, so run it from the
same folder as your other .py files (or adjust DB_PATH in remotetech_data.py).

Usage:
    python seed_admin.py
"""

import getpass
from remotetech_data import init_db, register_user

AVATAR_OPTIONS = ["🚀", "🦸", "🧑‍💻", "🌟", "🔥", "🛒", "🧪", "🏅"]


def main():
    init_db()  # make sure the users table exists

    print("=== RemoteTech Admin Account Setup ===\n")

    full_name = input("Full name: ").strip()
    username = input("Username: ").strip()
    email = input("Email: ").strip()

    # getpass hides the password as it's typed, instead of echoing it to the screen
    password = getpass.getpass("Password (min 8 characters): ")
    confirm_password = getpass.getpass("Confirm password: ")

    if not full_name or not username or not email or not password:
        print("\n❌ All fields are required. No account was created.")
        return

    if password != confirm_password:
        print("\n❌ Passwords do not match. No account was created.")
        return

    if len(password) < 8:
        print("\n❌ Password must be at least 8 characters. No account was created.")
        return

    print("\nChoose an avatar:")
    for i, avatar in enumerate(AVATAR_OPTIONS, start=1):
        print(f"  {i}. {avatar}")
    choice = input(f"Pick a number (1-{len(AVATAR_OPTIONS)}, default 1): ").strip()

    try:
        avatar = AVATAR_OPTIONS[int(choice) - 1]
    except (ValueError, IndexError):
        avatar = AVATAR_OPTIONS[0]

    success = register_user(
        full_name=full_name,
        username=username,
        email=email,
        password=password,
        avatar=avatar,
        role="admin",          # <-- the only place role="admin" should ever be set
        popia_consent=True,
    )

    if success:
        print(f"\n✅ Admin account '{username}' created successfully.")
        print("You can now log in through the Streamlit app with this account.")
    else:
        print(f"\n❌ Could not create account — username or email '{username}'/'{email}' already exists.")


if __name__ == "__main__":
    main()