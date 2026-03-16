from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL, FROM_NAME

conf = ConnectionConfig(
    MAIL_USERNAME=SMTP_USER or "dummy_user",
    MAIL_PASSWORD=SMTP_PASSWORD or "dummy_password",
    MAIL_FROM=FROM_EMAIL or "dummy@example.com",
    MAIL_PORT=SMTP_PORT or 587,
    MAIL_SERVER=SMTP_HOST or "smtp.example.com",
    MAIL_FROM_NAME=FROM_NAME or "Dummy Name",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL, FROM_NAME, FRONTEND_RESET_URL

async def send_reset_email(email_to: str, token: str):
    """
    Sends an email with a magic link for password reset.
    """
    reset_link = f"{FRONTEND_RESET_URL}?token={token}"
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #007bff;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>You requested a password reset. Please click the button below to set a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
                </div>
                <p>This link is valid for 15 minutes and can only be used once. If clicking the button doesn't work, copy and paste the following link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">If you did not request this reset, please ignore this email.</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
