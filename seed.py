from models import db
from app import app



# Create the app context and perform the database operation
if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()    