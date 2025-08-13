import feedparser
import os
import requests
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
RSS_URL = os.getenv("RSS_URL")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
USER_ID = os.getenv("USER_ID")  # Discord user ID
TIME_THRESHOLD_MINUTES = int(os.getenv("TIME_THRESHOLD_MINUTES"))  # minutes to consider as a new update

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
        if 'armory' in summary.lower():
            additional_note = '⚠️ARMORY MENTIONED⚠️'
        
        send_discord_notification(title, link, additional_note)
        
    else:
        print("Brak nowych aktualizacji.")

if __name__ == "__main__":
    main()
