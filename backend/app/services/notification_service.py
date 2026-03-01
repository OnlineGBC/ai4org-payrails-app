import logging
from datetime import datetime, timezone
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
    try:
        import brevo_python
        from brevo_python.rest import ApiException

        configuration = brevo_python.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_instance = brevo_python.TransactionalEmailsApi(
            brevo_python.ApiClient(configuration)
        )

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

        send_smtp_email = brevo_python.SendSmtpEmail(
            to=[{"email": to_email, "name": name}],
            sender={
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME,
            },
            subject=subject,
            html_content=html_content,
        )
        api_instance.send_transac_email(send_smtp_email)
        logger.info("Email sent to %s for txn status=%s", to_email, status)
    except Exception as e:
        logger.warning("notification_service: email send failed: %s", e)


def _send_sms(
    to_phone: str,
    status: str,
    amount: float,
    merchant_name: str,
) -> None:
    try:
        import brevo_python
        from brevo_python.rest import ApiException

        configuration = brevo_python.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_instance = brevo_python.TransactionalSMSApi(
            brevo_python.ApiClient(configuration)
        )

        message = f"PayRails: Your ${amount:,.2f} payment to {merchant_name} {status}."
        send_transac_sms = brevo_python.SendTransacSms(
            sender=settings.BREVO_SMS_SENDER,
            recipient=to_phone,
            content=message,
        )
        api_instance.send_transac_sms(send_transac_sms)
        logger.info("SMS sent to %s for status=%s", to_phone, status)
    except Exception as e:
        logger.warning("notification_service: SMS send failed: %s", e)
