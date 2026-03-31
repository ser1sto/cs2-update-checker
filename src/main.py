import feedparser
import json
import time
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import smtplib
from email.message import EmailMessage

load_dotenv()

# Load environment variables
RSS_URL = os.getenv("RSS_URL")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
USER_ID = os.getenv("USER_ID")  # discord user ID
TIME_THRESHOLD_MINUTES = int(os.getenv("TIME_THRESHOLD_MINUTES", "5"))  # minutes to consider as a new update
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # sender email
RECEIVER = os.getenv("RECEIVER")  # receiver email
pwd = os.getenv("EMAIL_PASSWORD") # google app password
if pwd and ((pwd.startswith("'") and pwd.endswith("'")) or (pwd.startswith('"') and pwd.endswith('"'))):
    pwd = pwd[1:-1]
EMAIL_PASSWORD = pwd
LAST_ENTRY_PATH = Path(os.getenv("LAST_ENTRY_PATH"))

def get_latest_rss_entry():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    newest_entries = feed.entries[0:3]
    newest_entries.sort(key=lambda x: x.published_parsed, reverse=True)

    return newest_entries[0].published_parsed, newest_entries[0].summary, newest_entries[0].link

def save_last_seen_date(parsed_time):
    temp_path = str(LAST_ENTRY_PATH) + '.tmp'
    data_to_save = list(parsed_time)

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, LAST_ENTRY_PATH)

    except Exception as e:
        print(f'Save error: {e}')
        if os.path.exists(temp_path):
            os.remove(temp_path)


def load_last_seen_date():
    if not LAST_ENTRY_PATH.exists():
        return time.struct_time((1970, 1, 1, 0, 0, 0, 0, 0, 0))

    try:
        with LAST_ENTRY_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
            return time.struct_time(tuple(data))

    except (json.JSONDecodeError, TypeError, ValueError, IOError):
        return time.struct_time((1970, 1, 1, 0, 0, 0, 0, 0, 0))


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
            print('Email sent!')
    except Exception as e:
        print(f'Email send error: {e}')


def send_discord_notification(link, armory_keyphrase=''):
    content = f"<@{USER_ID}> 📰 New CS2 update on Steam:\n**{link}**"
    if armory_keyphrase:
        content += f"\n\n**Warning:** {armory_keyphrase}"
    data = {
        "content": content,
        "username": "Jan Bot"
    }
    requests.post(WEBHOOK_URL, json=data, timeout=10)

def send_ntfy_notification():
    try:
        message = 'CS2 update contains Armory mention!'
        response = requests.post(NTFY_URL, data=message.encode('utf-8'), timeout=10)
        if response.status_code == 200:
            print('ntfy notification sent.')
        else:
            print(f'ntfy send error: {response.status_code}')
    except Exception as e:
        print(f'ntfy exception: {e}')


def monitor_updates():
    last_seen_date = load_last_seen_date()
    while True:
        try:
            result = get_latest_rss_entry()
            if result is None:
                print('Feed empty')

            else:
                new_entry_date, new_entry_summary, new_entry_link = result
                if new_entry_date > last_seen_date:
                    print('New update detected!')
                    last_seen_date = new_entry_date
                    save_last_seen_date(new_entry_date)
                    armory_check = ''
                    if 'armory' in new_entry_summary.lower():
                        armory_check = '⚠️ARMORY MENTIONED⚠️'
                        send_ntfy_notification()
                        send_email()

                    send_discord_notification(new_entry_link, armory_check)


        except Exception as e:
            print(e)

        time.sleep(TIME_THRESHOLD_MINUTES*60)


def main():
    print('starting app...')
    monitor_updates()

if __name__ == "__main__":
    main()