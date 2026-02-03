"""
Email Service - Send notifications via SMTP
"""
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)

# Brand color
BRAND_COLOR = "#009bc8"
BRAND_COLOR_DARK = "#007ca0"


class EmailService:
    """Service for sending email notifications"""

    @staticmethod
    def _get_base_styles() -> str:
        """Get base CSS styles for emails"""
        return """
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
            line-height: 1.6; 
            color: #374151; 
            margin: 0;
            padding: 0;
            background-color: #f3f4f6;
        }
        .wrapper {
            background-color: #f3f4f6;
            padding: 40px 20px;
        }
        .container { 
            max-width: 600px; 
            margin: 0 auto; 
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .header { 
            background: #ffffff; 
            padding: 30px; 
            text-align: center; 
            border-bottom: 1px solid #e5e7eb;
        }
        .header img {
            max-height: 60px;
            margin-bottom: 10px;
        }
        .header h1 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: #111827;
        }
        .content { 
            padding: 40px 30px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 24px;
        }
        .status-completed {
            background-color: #d1fae5;
            color: #065f46;
        }
        .status-failed {
            background-color: #fee2e2;
            color: #991b1b;
        }
        .info-table { 
            width: 100%;
            margin: 24px 0;
            border-collapse: collapse;
        }
        .info-table td {
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .info-table td:first-child {
            color: #6b7280;
            font-size: 14px;
            width: 40%;
        }
        .info-table td:last-child {
            color: #111827;
            font-weight: 500;
        }
        .button { 
            display: inline-block; 
            background: """ + BRAND_COLOR + """; 
            color: #ffffff !important; 
            padding: 14px 28px; 
            text-decoration: none; 
            border-radius: 6px; 
            font-weight: 500;
            font-size: 14px;
        }
        .button-secondary {
            background: #ffffff;
            color: """ + BRAND_COLOR + """ !important;
            border: 1px solid """ + BRAND_COLOR + """;
        }
        .button-container {
            text-align: center; 
            margin: 32px 0;
        }
        .button-container a {
            margin: 0 8px 8px 8px;
        }
        .message {
            background-color: #f9fafb;
            border-radius: 6px;
            padding: 16px;
            margin: 24px 0;
            font-size: 14px;
            color: #4b5563;
        }
        .error-message {
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
        }
        .footer { 
            text-align: center; 
            padding: 24px 30px;
            background-color: #f9fafb;
            border-top: 1px solid #e5e7eb;
        }
        .footer p {
            margin: 0;
            font-size: 12px;
            color: #9ca3af;
        }
        """

    @staticmethod
    async def send_job_completion_email(
        job_id: str,
        job_type: str,
        recipient_email: str,
        download_url: str,
        insight_url: str,
        total_documents: int,
        status: str = "completed",
        error_message: str = None
    ) -> bool:
        """
        Send job completion notification email.

        Args:
            job_id: Job UUID
            job_type: Type of job (tar_processing/pdf_splitting)
            recipient_email: Recipient email address
            download_url: URL to download result archive
            insight_url: URL to download insight XML
            total_documents: Number of documents processed
            status: Job status (completed/failed)
            error_message: Error message if job failed

        Returns:
            True if email sent successfully
        """
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning("SMTP not configured, skipping email")
            return False

        try:
            is_success = status == "completed"
            
            # Build email
            message = MIMEMultipart("alternative")
            
            if is_success:
                message["Subject"] = f"LudwigOne: Verarbeitung abgeschlossen - {total_documents} Dokumente"
            else:
                message["Subject"] = f"LudwigOne: Verarbeitung fehlgeschlagen - Job {job_id[:8]}"
            
            message["From"] = settings.smtp_username
            message["To"] = recipient_email

            # Format job type for display
            job_type_display = "TAR-Archiv Verarbeitung" if job_type == "tar_processing" else "PDF Splitting"

            # Plain text version
            if is_success:
                text_content = f"""
LudwigOne - Dokumentenverarbeitung

Status: Erfolgreich abgeschlossen

Job-Details:
- Job ID: {job_id}
- Typ: {job_type_display}
- Verarbeitete Dokumente: {total_documents}

Ergebnisse herunterladen: {download_url}
Insight-Report ansehen: {insight_url}

---
LudwigOne - Intelligente Dokumentenverarbeitung
"""
            else:
                text_content = f"""
LudwigOne - Dokumentenverarbeitung

Status: Fehlgeschlagen

Job-Details:
- Job ID: {job_id}
- Typ: {job_type_display}

Fehlermeldung: {error_message or 'Unbekannter Fehler'}

Bitte versuchen Sie es erneut oder kontaktieren Sie den Support.

---
LudwigOne - Intelligente Dokumentenverarbeitung
"""

            # HTML version
            styles = EmailService._get_base_styles()
            
            if is_success:
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{styles}</style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <h1>LudwigOne</h1>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="status-badge status-completed">Erfolgreich abgeschlossen</span>
                </div>
                
                <p style="text-align: center; color: #6b7280; margin-bottom: 32px;">
                    Ihre Dokumente wurden erfolgreich verarbeitet und kategorisiert.
                </p>

                <table class="info-table">
                    <tr>
                        <td>Job ID</td>
                        <td>{job_id[:8]}...</td>
                    </tr>
                    <tr>
                        <td>Verarbeitungstyp</td>
                        <td>{job_type_display}</td>
                    </tr>
                    <tr>
                        <td>Verarbeitete Dokumente</td>
                        <td>{total_documents}</td>
                    </tr>
                </table>

                <div class="button-container">
                    <a href="{download_url}" class="button">Ergebnisse herunterladen</a>
                    <a href="{insight_url}" class="button button-secondary">Insight-Report</a>
                </div>

                <div class="message">
                    Die Dokumente wurden automatisch analysiert, kategorisiert und entsprechend umbenannt. 
                    Im Insight-Report finden Sie eine detaillierte Übersicht aller Verarbeitungsschritte.
                </div>
            </div>
            <div class="footer">
                <p>LudwigOne - Intelligente Dokumentenverarbeitung</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
            else:
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{styles}</style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <h1>LudwigOne</h1>
            </div>
            <div class="content">
                <div style="text-align: center;">
                    <span class="status-badge status-failed">Verarbeitung fehlgeschlagen</span>
                </div>
                
                <p style="text-align: center; color: #6b7280; margin-bottom: 32px;">
                    Bei der Verarbeitung Ihrer Dokumente ist ein Fehler aufgetreten.
                </p>

                <table class="info-table">
                    <tr>
                        <td>Job ID</td>
                        <td>{job_id[:8]}...</td>
                    </tr>
                    <tr>
                        <td>Verarbeitungstyp</td>
                        <td>{job_type_display}</td>
                    </tr>
                </table>

                <div class="message error-message">
                    <strong>Fehlermeldung:</strong><br>
                    {error_message or 'Ein unbekannter Fehler ist aufgetreten.'}
                </div>

                <p style="text-align: center; color: #6b7280; font-size: 14px;">
                    Bitte versuchen Sie es erneut. Sollte das Problem weiterhin bestehen, 
                    kontaktieren Sie bitte den Support mit der oben genannten Job ID.
                </p>
            </div>
            <div class="footer">
                <p>LudwigOne - Intelligente Dokumentenverarbeitung</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=True
            )

            logger.info(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Global instance
email_service = EmailService()
