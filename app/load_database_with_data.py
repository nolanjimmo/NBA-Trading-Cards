import os

from app import db_filename
from app.query_engine import load_database, load_test_data

if __name__ == "__main__":
    if os.path.exists(db_filename):
        print("Deleting old database")
        os.remove(db_filename)

    print("Creating Database")
    load_database()

    print("Loading test data")
    load_test_data()

    print("Done!")
