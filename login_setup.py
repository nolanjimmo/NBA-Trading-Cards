"""
Do a little setup!
"""

from login_db import create_db


if __name__ == '__main__':
    print("Initializing database...")
    create_db()

    print("Done!")
