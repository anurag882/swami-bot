import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import unicodedata
import random
import time
from fake_useragent import UserAgent

ua = UserAgent()
headers = {
    "User-Agent": ua.random,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
}

session = requests.Session()
session.headers.update(headers)

# In-memory cache to avoid duplicate posts (bonus)
seen_notices = set()

districts = [
    "jashpur", "raipur", "bastar", "bilaspur", "durg", "rajnandgaon", "kondagaon", "kabirdham",
    "balod", "baloda-bazar", "balrampur", "bametara", "bijapur", "dantewada", "gariaband", "gaurela-pendra-marwahi",
    "janjgir-champa", "kanker", "korba", "koriya", "mahasamund", "mungeli", "narayanpur", "raigarh", "sukma", "surajpur", "surguja"
]

def normalize_text(text):
    return unicodedata.normalize("NFKC", text.strip())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /jobs to get Swami Atmanand job updates.")

def get_swami_jobs(district):
    url = f"https://{district}.nic.in/notice_category/भरती"
    try:
        # Rotate User-Agent for each request
        session.headers["User-Agent"] = ua.random
        # Polite delay (5–10 seconds)
        time.sleep(random.uniform(5, 10))
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        notices = []
        # Scan all relevant tags
        tags = soup.find_all(["li", "div", "p", "a"])
        for tag in tags:
            text = normalize_text(tag.get_text(" ", strip=True))
            if "स्वामी आत्मानंद" in text:
                # Try to find a link
                link_tag = tag.find("a") if tag.name != "a" else tag
                link = link_tag["href"] if link_tag and link_tag.has_attr("href") else url
                # Avoid duplicates using a hash of (district, text, link)
                notice_id = f"{district}|{text}|{link}"
                if notice_id in seen_notices:
                    continue
                seen_notices.add(notice_id)
                notices.append({
                    "district": district,
                    "title": text,
                    "link": link
                })
        return notices
    except Exception as e:
        logging.error(f"Failed for {district}: {e}")
        return []


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching Swami Atmanand job listings... please wait ⏳")
    results = []
    for district in districts:
        results.extend(get_swami_jobs(district))
    if results:
        for msg in results[:10]:  # Send first 10 jobs
            # Markdown formatting
            message = f"*District:* {msg['district'].title()}\n*Title:* {msg['title']}\n[View Notice]({msg['link']})"
            await update.message.reply_markdown(message, disable_web_page_preview=True)
    else:
        await update.message.reply_text("No jobs found mentioning 'स्वामी आत्मानंद' right now.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BOT_TOKEN = "8030767533:AAF1hEY6_5bpTOMwipEMk6eChHxPm7fSy6E"
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.run_polling()
