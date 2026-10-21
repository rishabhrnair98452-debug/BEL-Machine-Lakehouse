import getpass

from auth import init_auth_db, create_user, DATABASE

init_auth_db()

print("\n=== BEL Dashboard: Admin Setup ===")
print("Database:", DATABASE)

username = input("Enter Admin username: ").strip()
password = getpass.getpass("Create Admin password (minimum 12 characters): ")
confirm = getpass.getpass("Confirm Admin password: ")

if password != confirm:
    print("Passwords do not match. Please try again.")
elif len(password) < 12:
    print("Password must contain at least 12 characters.")
else:
    try:
        create_user(username, password, "Admin")
        print(f"\nAdmin account '{username}' created successfully!")

    except Exception as exc:
        print("\nCould not create Admin account:", exc)