import feedparser
import json
import time
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import smtplib
from email.message import EmailMessage
from prometheus_client import start_http_server, Counter, Gauge, Summary

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

# Define Prometheus metrics
PROM_CHECKS = Counter('bot_rss_checks_total', 'Total number of RSS feed check cycles started')
PROM_RESPONSES = Counter('bot_rss_responses_total', 'Statistics of RSS responses', ['result'])
PROM_PROCESS_TIME = Summary('bot_processing_duration_seconds', 'Time spent processing the RSS feed and sending notifications')
PROM_ERRORS = Counter('bot_errors_total', 'Total count of errors broken down by module type', ['type'])
PROM_UPDATES = Counter('bot_updates_detected_total', 'Count of actual game updates detected')
PROM_LAST_UPDATE_TIME = Gauge('bot_last_update_timestamp_seconds', 'Unix timestamp of the last detected update')

# Init Prometheus metrics
PROM_RESPONSES.labels(result='success').inc(0)
PROM_RESPONSES.labels(result='empty').inc(0)
PROM_ERRORS.labels(type='rss_parse').inc(0)
PROM_ERRORS.labels(type='disk_write').inc(0)
PROM_ERRORS.labels(type='email').inc(0)
PROM_ERRORS.labels(type='discord').inc(0)
PROM_ERRORS.labels(type='ntfy').inc(0)
PROM_ERRORS.labels(type='general_loop').inc(0)
PROM_CHECKS.inc(0)
PROM_UPDATES.inc(0)


def get_latest_rss_entry():
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            return None
        newest_entries = feed.entries[0:3]
        newest_entries.sort(key=lambda x: x.published_parsed, reverse=True)
        return newest_entries[0].published_parsed, newest_entries[0].summary, newest_entries[0].link
    except Exception as e:
        PROM_ERRORS.labels(type='rss_parse').inc()
        print(f'Parse error: {e}')

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
        PROM_ERRORS.labels(type='disk_write').inc()
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
        PROM_ERRORS.labels(type='email').inc()
        print(f'Email send error: {e}')


def send_discord_notification(link, armory_keyphrase=''):
    try:
        content = f"<@{USER_ID}> 📰 New CS2 update on Steam:\n**{link}**"
        if armory_keyphrase:
            content += f"\n\n**Warning:** {armory_keyphrase}"
        data = {
            "content": content,
            "username": "Jan Bot"
        }
        requests.post(WEBHOOK_URL, json=data, timeout=10)
    
    except Exception as e:
        PROM_ERRORS.labels(type='discord').inc()
        print(f'Discord send error: {e}')


def send_ntfy_notification():
    try:
        message = 'CS2 update contains Armory mention!'
        response = requests.post(NTFY_URL, data=message.encode('utf-8'), timeout=10)
        if response.status_code == 200:
            print('ntfy notification sent.')
        else:
            print(f'ntfy send error: {response.status_code}')
    except Exception as e:
        PROM_ERRORS.labels(type='ntfy').inc()
        print(f'ntfy send error: {e}')


def monitor_updates():
    last_seen_date = load_last_seen_date()
    if last_seen_date:
        PROM_LAST_UPDATE_TIME.set(time.mktime(last_seen_date))

    while True:
        PROM_CHECKS.inc()
        start_time = time.time()
        try:
            result = get_latest_rss_entry()
            if result is None:
                PROM_RESPONSES.labels(result='empty').inc()
                print('Feed empty')

            else:
                PROM_RESPONSES.labels(result='success').inc()
                new_entry_date, new_entry_summary, new_entry_link = result
                if new_entry_date > last_seen_date:
                    print('New update detected!')
                    PROM_UPDATES.inc()
                    PROM_LAST_UPDATE_TIME.set(time.mktime(new_entry_date))
                    last_seen_date = new_entry_date
                    save_last_seen_date(new_entry_date)
                    armory_check = ''
                    if 'armory' in new_entry_summary.lower():
                        armory_check = '⚠️ARMORY MENTIONED⚠️'
                        send_ntfy_notification()
                        send_email()

                    send_discord_notification(new_entry_link, armory_check)


        except Exception as e:
            PROM_ERRORS.labels(type='general_loop').inc()
            print(e)

        duration = time.time() - start_time
        PROM_PROCESS_TIME.observe(duration)
        time.sleep(TIME_THRESHOLD_MINUTES*60)


def main():
    print('starting app...')
    print('starting Prometheus metrics on port 8000...')
    start_http_server(8000)
    monitor_updates()

if __name__ == "__main__":
    main()