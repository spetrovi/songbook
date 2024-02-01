import argparse
from getpass import getpass

from app.users.models import User as UserModel


def create_superuser():
    """
    Create a superuser in the database
    """
    email = input("Enter superuser email: ")
    password = getpass("Enter superuser password: ")

    try:
        UserModel.create_user(email, password, is_admin=True)
        print(f"Superuser {email} created successfully.")
    except Exception as e:
        print(f"Error creating superuser: {e}")


def main():
    parser = argparse.ArgumentParser(description="Simple management for database")

    parser.add_argument(
        "--createsuperuser", action="store_true", help="Create a superuser"
    )
    args = parser.parse_args()

    if args.createsuperuser:
        create_superuser()


if __name__ == "__main__":
    main()
