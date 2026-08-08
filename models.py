from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Attendee(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True)

    phone = db.Column(db.String(20))

    event = db.Column(db.String(100))

    category = db.Column(db.String(50))

    checkin = db.Column(db.Boolean, default=False)

    qr_code = db.Column(db.String(200))

    registration_id = db.Column(db.String(20), unique=True)

    checkin_time = db.Column(db.DateTime)

    def __repr__(self):
        return self.name