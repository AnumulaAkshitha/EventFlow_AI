from models import Attendee


class RegistrationAgent:
    """
    AI-assisted registration agent.

    Responsible for:
    - Validating registration data
    - Checking duplicate email
    - Checking duplicate phone
    - Validating event and category
    - Returning a registration decision
    """

    VALID_EVENTS = [
        "AI Workshop",
        "Hackathon",
        "Cloud Summit"
    ]

    VALID_CATEGORIES = [
        "Student",
        "Professional",
        "Speaker"
    ]

    def validate(self, name, email, phone, event, category):

        errors = []

        # -----------------------------
        # Name validation
        # -----------------------------

        if not name:
            errors.append("Name is required.")

        elif len(name) < 3:
            errors.append("Name must contain at least 3 characters.")

        # -----------------------------
        # Email validation
        # -----------------------------

        if not email:
            errors.append("Email is required.")

        elif "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")

        # -----------------------------
        # Phone validation
        # -----------------------------

        if not phone:
            errors.append("Phone number is required.")

        elif not phone.isdigit():
            errors.append("Phone number must contain only digits.")

        elif len(phone) != 10:
            errors.append("Phone number must contain 10 digits.")

        # -----------------------------
        # Event validation
        # -----------------------------

        if event not in self.VALID_EVENTS:
            errors.append("Invalid event selected.")

        # -----------------------------
        # Category validation
        # -----------------------------

        if category not in self.VALID_CATEGORIES:
            errors.append("Invalid category selected.")

        return errors

    def check_duplicates(self, email, phone):

        errors = []

        existing_email = Attendee.query.filter_by(
            email=email
        ).first()

        if existing_email:
            errors.append(
                "This email is already registered."
            )

        existing_phone = Attendee.query.filter_by(
            phone=phone
        ).first()

        if existing_phone:
            errors.append(
                "This phone number is already registered."
            )

        return errors

    def process_registration(
        self,
        name,
        email,
        phone,
        event,
        category
    ):

        # Basic validation
        errors = self.validate(
            name,
            email,
            phone,
            event,
            category
        )

        if errors:

            return {
                "success": False,
                "errors": errors
            }

        # Duplicate checking
        duplicate_errors = self.check_duplicates(
            email,
            phone
        )

        if duplicate_errors:

            return {
                "success": False,
                "errors": duplicate_errors
            }

        # Registration approved
        return {
            "success": True,
            "errors": [],
            "message": (
                "Registration data validated successfully."
            )
        }