from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolInputSchema, ToolResult
from app.core.logging import get_logger

logger = get_logger("tools.send_email")


class SendEmailInput(ToolInputSchema):
    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email to a recipient"
    input_schema = SendEmailInput
    required_permissions = ["email:send"]

    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.smtp_config = smtp_config or {}

    def run(self, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None) -> ToolResult:
        if not self.smtp_config:
            return ToolResult(success=False, error="SMTP configuration not provided", metadata={"simulated": True, "to": to, "subject": subject})
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.smtp_config.get("from_email", "noreply@example.com")
            msg["To"] = to
            if cc:
                msg["Cc"] = cc
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                if self.smtp_config.get("use_tls"):
                    server.starttls()
                if self.smtp_config.get("username") and self.smtp_config.get("password"):
                    server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            logger.info(f"Email sent to {to}")
            return ToolResult(success=True, data={"to": to, "subject": subject})
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return ToolResult(success=False, error=str(e))
