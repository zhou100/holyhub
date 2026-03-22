from holyhub.database import Database

db = Database()


def get_db() -> Database:
    return db
