import feedparser
import os
import requests
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

# Load environment variables
RSS_URL = os.getenv("RSS_URL")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
USER_ID = os.getenv("USER_ID")  # Discord user ID
TIME_THRESHOLD_MINUTES = int(os.getenv("TIME_THRESHOLD_MINUTES"))  # minutes to consider as a new update
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # sender email
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # google app password
RECEIVER = os.getenv("RECEIVER")  # receiver email


def send_email():
    msg = EmailMessage()
    msg['Subject'] = 'Armory update detected!'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER
    msg.set_content('Armory update detected!')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("E-mail został pomyślnie wysłany!")
    except Exception as e:
        print(f"Wystąpił błąd podczas wysyłania e-maila: {e}")

def get_latest_rss_entry():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    pub_date = parsedate_to_datetime(entry.published)
    summary = str(entry.summary)
    return pub_date, entry.title, entry.link, summary

def send_discord_notification(title, link, summary_keyphrase=''):
    content = f"<@{USER_ID}> 📰 Nowa aktualizacja CS2 na Steam:\n**{title}**\n{link}"
    if summary_keyphrase:
        content += f"\n\n**Podsumowanie:** {summary_keyphrase}"
    data = {
        "content": content,
        "username": "Jan Bot"
    }
    requests.post(WEBHOOK_URL, json=data)

def send_ntfy_notification(message):
    try:
        response = requests.post(NTFY_URL, data=message.encode('utf-8'))
        if response.status_code == 200:
            print("Powiadomienie ntfy wysłane.")
        else:
            print(f"Błąd wysyłania ntfy: {response.status_code}")
    except Exception as e:
        print(f"Wyjątek przy wysyłaniu ntfy: {e}")

def main():
    print("Sprawdzanie RSS CS2...")
    result = get_latest_rss_entry()
    if not result:
        print("Błąd pobierania danych RSS.")
        return

    pub_date, title, link, summary = result
    now = datetime.now(timezone.utc)
    delta = now - pub_date

    print(f"Data publikacji: {pub_date.isoformat()} | Różnica: {delta}")

    if delta <= timedelta(minutes=TIME_THRESHOLD_MINUTES):
        print("Wykryto nową aktualizację!")

        additional_note = ''
        if 'to' in summary.lower():
            additional_note = '⚠️ARMORY MENTIONED⚠️'
            send_ntfy_notification('Aktualizacja CS2 zawiera wzmiankę o Armory!')
            send_email()
        
        send_discord_notification(title, link, additional_note)
        
    else:
        print("Brak nowych aktualizacji.")

if __name__ == "__main__":
    main()
