from bs4 import BeautifulSoup
import cloudscraper
import unicodedata


url = "http://jashpur.nic.in/en/notice_category/recruitment"  # use http
scraper = cloudscraper.create_scraper()

r = scraper.get(url, timeout=20)
soup = BeautifulSoup(r.text, "html.parser")

for tag in soup.find_all(["li", "p", "div", "a"]):
    text = unicodedata.normalize("NFKC", tag.get_text(" ", strip=True))
    if "स्वामी आत्मानंद" in text or "Swami Atmanand" in text:
        print("🟢 FOUND:", text)

