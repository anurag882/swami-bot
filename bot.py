import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import unicodedata
import random
import time
from fake_useragent import UserAgent
import os

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
    "Balod", "Baloda Bazar", "Balrampur-Ramanujganj", "Bastar", "Bemetara",
    "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg",
    "Gariaband", "Gaurela‑Pendra‑Marwahi", "Janjgir‑Champa", "Jashpur", "Kabirdham (Kawardha)",
    "Kanker", "Kondagaon", "Korba", "Koriya (Korea)", "Mahasamund",
    "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon",
    "Sakti", "Sukma", "Surajpur", "Surguja"
]

recruitment_urls = {
    "Balod": "http://balod.gov.in/en/notice_category/recruitment/",
    "Baloda Bazar": "https://balodabazar.gov.in/en/notice_category/recruitment/",
    "Balrampur-Ramanujganj": "http://balrampur.gov.in/en/notice_category/recruitment/",
    "Bastar": "http://bastar.gov.in/en/notice_category/recruitment/",
    "Bemetara": "http://bemetara.gov.in/en/notice_category/recruitment/",
    "Bijapur": "http://bijapur.gov.in/en/notice_category/recruitment/",
    "Bilaspur": "http://bilaspur.gov.in/en/notice_category/recruitment/",
    "Dantewada": "http://dantewada.gov.in/en/notice_category/recruitment/",
    "Dhamtari": "http://dhamtari.gov.in/en/notice_category/recruitment/",
    "Durg": "http://durg.gov.in/en/notice_category/recruitment/",
    "Gariaband": "http://gariaband.gov.in/en/notice_category/recruitment/",
    "Gaurela‑Pendra‑Marwahi": "https://gaurela-pendra-marwahi.cg.gov.in/en/notice_category/recruitment/",
    "Janjgir‑Champa": "http://janjgir-champa.gov.in/en/notice_category/recruitment/",
    "Jashpur": "https://jashpur.nic.in/en/notice_category/recruitment/",
    "Kabirdham (Kawardha)": "http://kawardha.gov.in/en/notice_category/recruitment/",
    "Kanker": "http://kanker.gov.in/en/notice_category/recruitment/",
    "Kondagaon": "http://kondagaon.gov.in/en/notice_category/recruitment/",
    "Korba": "http://korba.gov.in/en/notice_category/recruitment/",
    "Koriya (Korea)": "http://korea.gov.in/en/notice_category/recruitment/",
    "Mahasamund": "http://mahasamund.gov.in/en/notice_category/recruitment/",
    "Mungeli": "http://mungeli.gov.in/en/notice_category/recruitment/",
    "Narayanpur": "http://narayanpur.gov.in/en/notice_category/recruitment/",
    "Raigarh": "http://raigarh.gov.in/en/notice_category/recruitment/",
    "Raipur": "http://raipur.gov.in/en/notice_category/recruitment/",
    "Rajnandgaon": "http://rajnandgaon.gov.in/en/notice_category/recruitment/",
    "Sakti": "https://sakti.cg.gov.in/en/notice_category/recruitment/",
    "Sukma": "https://sukma.gov.in/en/notice_category/recruitment/",
    "Surajpur": "http://surajpur.gov.in/en/notice_category/recruitment/",
    "Surguja": "http://surguja.gov.in/en/notice_category/recruitment/"
}




def normalize_text(text):
    return unicodedata.normalize("NFKC", text.strip())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /jobs to get Swami Atmanand job updates.")

def get_swami_jobs(district):
    url = recruitment_urls.get(district)
    try:
        # Rotate User-Agent for each request
        session.headers["User-Agent"] = ua.random
        # Polite delay (5–10 seconds)
        time.sleep(random.uniform(5, 10))
        r = session.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        notices = []
        # Scan all relevant tags
        tags = soup.find_all(["li", "div", "p", "a"])
        for tag in tags:
            text = normalize_text(tag.get_text(" ", strip=True))
            text = text.replace("भरती", "भर्ती")  # Normalize to "भर्ती"
            # Check if the text contains "स्वामी आत्मानंद" or "Swami Atmanand"
            # and avoid duplicates  
            if "स्वामी आत्मानंद" in text or "Swami Atmanand" in text:
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
    progress_msg = await update.message.reply_text("Fetching Swami Atmanand job listings... please wait ⏳")
    found_districts = []
    failed_districts = []
    total = len(districts)
    for idx, district in enumerate(districts, 1):
        notices = get_swami_jobs(district)
        if notices:
            found_districts.append(district)
        elif notices == []:
            # If the notices list is empty, check if it was due to an error (logged)
            # We'll treat all empty results as possible failures for reporting
            url = recruitment_urls.get(district)
            try:
                # Try a simple request to see if the site is up
                session.get(url, timeout=5)
            except Exception:
                failed_districts.append(district)
        # Update progress bar
        bar_len = 20
        filled_len = int(bar_len * idx // total)
        bar = "█" * filled_len + "░" * (bar_len - filled_len)
        progress_text = f"Progress: [{bar}] {idx}/{total} districts checked"
        await progress_msg.edit_text(progress_text)
    # Prepare result message
    if found_districts:
        district_list = "\n".join(
            f"- [{d.title()}]({recruitment_urls[d]})"
            for d in found_districts
        )
        message = f"Districts with Swami Atmanand job postings:\n{district_list}"
    else:
        message = "No districts found with 'स्वामी आत्मानंद' job postings right now."
    # Add failed districts info
    if failed_districts:
        failed_list = "\n".join(f"- {d.title()}" for d in failed_districts)
        message += f"\n\n❗ Failed to fetch from these districts:\n{failed_list}"
    await progress_msg.edit_text(message, disable_web_page_preview=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.run_polling()
