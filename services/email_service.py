import os
import smtplib

from email.message import EmailMessage
from email.utils import formataddr


class EmailService:

    def __init__(self):

        self.mail_username = os.getenv("MAIL_USERNAME")
        self.mail_password = os.getenv("MAIL_PASSWORD")

        self.mail_server = os.getenv(
            "MAIL_SERVER",
            "smtp.gmail.com"
        )

        self.mail_port = int(
            os.getenv("MAIL_PORT", 587)
        )

    def send_registration_confirmation(
        self,
        attendee,
        registration_id,
        qr_path
    ):

        if not self.mail_username or not self.mail_password:

            return {
                "success": False,
                "message": "Email credentials are not configured."
            }

        try:

            message = EmailMessage()

            message["Subject"] = (
                f"EventFlow AI - Registration Confirmed "
                f"({registration_id})"
            )

            message["From"] = formataddr(
                ("EventFlow AI", self.mail_username)
            )

            message["To"] = attendee.email

            message.set_content(
                f"""
Hello {attendee.name},

Your registration for EventFlow AI has been successfully confirmed.

Registration Details
----------------------------

Registration ID: {registration_id}
Event: {attendee.event}
Category: {attendee.category}

Please keep this email and your QR code safe.

You can use the QR code for event check-in.

Thank you for registering with EventFlow AI.

Regards,
EventFlow AI
Intelligent Event Management Platform
"""
            )

            # Attach QR code
            if qr_path and os.path.exists(qr_path):

                with open(qr_path, "rb") as qr_file:

                    qr_data = qr_file.read()

                message.add_attachment(
                    qr_data,
                    maintype="image",
                    subtype="png",
                    filename=f"{registration_id}.png"
                )

            # Connect to Gmail SMTP
            with smtplib.SMTP(
                self.mail_server,
                self.mail_port
            ) as server:

                server.starttls()

                server.login(
                    self.mail_username,
                    self.mail_password
                )

                server.send_message(message)

            return {
                "success": True,
                "message": "Confirmation email sent successfully."
            }

        except Exception as e:

            print("Email Error:", e)

            return {
                "success": False,
                "message": str(e)
            }