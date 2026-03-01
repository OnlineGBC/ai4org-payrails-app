import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


def notify_transaction(
    db: Session,
    user_id: str,
    txn_id: str,
    status: str,
    amount: float,
    merchant_name: str,
    rail: str,
    description: str | None,
) -> None:
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    _send_email(
        to_email=user.email,
        name=user.email,
        status=status,
        amount=amount,
        merchant_name=merchant_name,
        rail=rail,
        description=description,
    )

    if user.phone:
        _send_sms(
            to_phone=user.phone,
            status=status,
            amount=amount,
            merchant_name=merchant_name,
        )


def _send_email(
    to_email: str,
    name: str,
    status: str,
    amount: float,
    merchant_name: str,
    rail: str,
    description: str | None,
) -> None:
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.debug("notification_service: SMTP credentials not configured, skipping email")
        return

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        subject = f"Transaction {status.upper()}: ${amount:,.2f} to {merchant_name}"
        html_content = f"""
        <html><body>
        <h2>PayRails Transaction Notification</h2>
        <p>Hello {name},</p>
        <p>Your transaction has been <strong>{status}</strong>.</p>
        <table style="border-collapse:collapse;width:100%">
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Amount</strong></td>
              <td style="padding:8px;border:1px solid #ddd">${amount:,.2f}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Merchant</strong></td>
              <td style="padding:8px;border:1px solid #ddd">{merchant_name}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Rail</strong></td>
              <td style="padding:8px;border:1px solid #ddd">{rail.upper()}</td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Status</strong></td>
              <td style="padding:8px;border:1px solid #ddd">{status}</td></tr>
          {"<tr><td style='padding:8px;border:1px solid #ddd'><strong>Description</strong></td><td style='padding:8px;border:1px solid #ddd'>" + description + "</td></tr>" if description else ""}
          <tr><td style="padding:8px;border:1px solid #ddd"><strong>Timestamp</strong></td>
              <td style="padding:8px;border:1px solid #ddd">{timestamp}</td></tr>
        </table>
        <p style="color:#888;font-size:12px;margin-top:24px">
          MVP Demo Environment — All transactions are simulated.
        </p>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SENDER_NAME} <{settings.FROM_ADDR}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        if settings.SMTP_USE_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.FROM_ADDR, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.FROM_ADDR, to_email, msg.as_string())

        logger.info("Email sent to %s for txn status=%s", to_email, status)
    except Exception as e:
        logger.warning("notification_service: email send failed: %s", e)


def _send_sms(
    to_phone: str,
    status: str,
    amount: float,
    merchant_name: str,
) -> None:
    if not settings.BREVO_API_KEY:
        logger.debug("notification_service: BREVO_API_KEY not configured, skipping SMS")
        return

    try:
        import httpx

        message = f"PayRails: Your ${amount:,.2f} payment to {merchant_name} {status}."
        response = httpx.post(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            json={
                "sender": settings.BREVO_SMS_SENDER,
                "recipient": to_phone,
                "content": message,
            },
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info("SMS sent to %s for status=%s", to_phone, status)
    except Exception as e:
        logger.warning("notification_service: SMS send failed: %s", e)
