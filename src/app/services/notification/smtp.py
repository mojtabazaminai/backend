import aiosmtplib
from email.message import EmailMessage

from ...core.config import settings
from ...schemas.notification import EmailPayload


class SMTPClient:
    def __init__(self) -> None:
        self.hostname = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send(self, payload: EmailPayload) -> None:
        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = payload.to
        message["Subject"] = payload.subject
        
        if payload.cc:
            message["Cc"] = ", ".join(payload.cc)
        if payload.bcc:
            message["Bcc"] = ", ".join(payload.bcc)

        message.set_content(payload.body, subtype="html")

        # Configure connection arguments
        smtp_args: dict = {
            "hostname": self.hostname,
            "port": self.port,
        }

        if settings.SMTP_SSL:
            # Implicit SSL/TLS (usually port 465)
            smtp_args["use_tls"] = True
        elif settings.SMTP_TLS:
            # STARTTLS (usually port 587) - auto-negotiated by aiosmtplib
            smtp_args["use_tls"] = False
            smtp_args["start_tls"] = True
        else:
            smtp_args["use_tls"] = False

        async with aiosmtplib.SMTP(**smtp_args) as smtp:
            if self.username and self.password:
                await smtp.login(self.username, self.password)

            await smtp.send_message(message)
