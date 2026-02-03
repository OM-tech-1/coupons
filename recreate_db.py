from app.database import engine, Base
from app.models.user import User

print("Dropping users table...")
User.__table__.drop(engine)
print("Users table dropped.")

print("Recreating tables...")
Base.metadata.create_all(bind=engine)
print("Tables recreated.")
