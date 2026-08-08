import re
from models import Attendee


class ValidationService:

    @staticmethod
    def validate_name(name):

        name = name.strip()

        if len(name) < 3:
            return False, "Name must contain at least 3 characters."

        if not re.fullmatch(r"[A-Za-z ]+", name):
            return False, "Name should contain only letters and spaces."

        return True, ""


    @staticmethod
    def validate_email(email):

        email = email.strip().lower()

        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.fullmatch(pattern, email):
            return False, "Invalid email format."

        return True, ""


    @staticmethod
    def validate_phone(phone):

        phone = phone.strip()

        if not re.fullmatch(r"[6-9]\d{9}", phone):
            return False, "Phone number must be a valid 10-digit Indian mobile number."

        return True, ""


    @staticmethod
    def validate_event(event):

        allowed = [
            "AI Workshop",
            "Hackathon",
            "Cloud Summit"
        ]

        if event not in allowed:
            return False, "Please select a valid event."

        return True, ""


    @staticmethod
    def validate_category(category):

        allowed = [
            "Student",
            "Professional",
            "Speaker"
        ]

        if category not in allowed:
            return False, "Please select a valid category."

        return True, ""


    @staticmethod
    def check_duplicate_email(email):

        attendee = Attendee.query.filter_by(email=email).first()

        if attendee:
            return False, "This email is already registered."

        return True, ""


    @staticmethod
    def check_duplicate_phone(phone):

        attendee = Attendee.query.filter_by(phone=phone).first()

        if attendee:
            return False, "This phone number is already registered."

        return True, ""