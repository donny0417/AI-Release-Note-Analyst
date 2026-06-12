from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import os
import re
import smtplib

REPORT_PATTERN = re.compile(r"^\d{4}/ai-release-report-\d{4}-\d{2}-\d{2}(?:-v\d+)?\.html$")

def find_latest_report() -> Path:
    candidates = []

    for path in Path(".").glob("20*/ai-release-report-*.html"):
        normalized = path.as_posix()
        if REPORT_PATTERN.match(normalized):
            candidates.append(path)

    if not candidates:
        raise FileNotFoundError("No weekly AI release report HTML file found.")

    return sorted(candidates, key=lambda p: p.as_posix())[-1]

def build_subject(report_path: Path) -> str:
    match = re.search(r"ai-release-report-(\d{4}-\d{2}-\d{2})(?:-v\d+)?\.html", report_path.name)
    report_date = match.group(1) if match else "latest"
    return f"[Weekly AI Release Report] {report_date}"

def main():
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients = [email.strip() for email in os.environ["MAIL_TO"].split(",") if email.strip()]
    from_name = os.environ.get("MAIL_FROM_NAME", "AI Release Note Analyst")

    report_path = find_latest_report()
    html = report_path.read_text(encoding="utf-8")

    message = MIMEMultipart("alternative")
    message["Subject"] = build_subject(report_path)
    message["From"] = f"{from_name} <{gmail_user}>"
    message["To"] = ", ".join(recipients)

    text_fallback = f"이번 주 AI Release Report입니다.\n\nGitHub report file: {report_path.as_posix()}"
    message.attach(MIMEText(text_fallback, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, message.as_string())

    print(f"Sent {report_path.as_posix()} to {', '.join(recipients)}")

if __name__ == "__main__":
    main()
