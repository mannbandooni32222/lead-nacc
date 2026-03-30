import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# -------------------------------
# CONFIG
# -------------------------------
EMAIL_REGEX = r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+"
PHONE_REGEX = r"\+?\d[\d\s\-]{8,}\d"

SOCIAL_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def extract_username(url):
    try:
        path = urlparse(url).path.strip("/")
        return path.split("/")[0]
    except:
        return ""

def scrape_page(url):
    data = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()

        emails = list(set(re.findall(EMAIL_REGEX, text)))
        phones = list(set(re.findall(PHONE_REGEX, text)))

        links = [a.get("href") for a in soup.find_all("a", href=True)]

        for link in links:
            full_link = urljoin(url, link)

            entry = {
                "Website": url,
                "Email": ", ".join(emails),
                "Phone": ", ".join(phones),
                "Social Link": "",
                "Username": ""
            }

            if any(domain in full_link for domain in SOCIAL_DOMAINS):
                entry["Social Link"] = full_link
                entry["Username"] = extract_username(full_link)

            data.append(entry)

        return data

    except Exception as e:
        return [{"Website": url, "Error": str(e)}]

def crawl_website(start_url, max_pages=5):
    visited = set()
    to_visit = [start_url]
    all_data = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)

        if url in visited:
            continue

        visited.add(url)

        page_data = scrape_page(url)
        all_data.extend(page_data)

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])

                if urlparse(link).netloc == urlparse(start_url).netloc:
                    if link not in visited:
                        to_visit.append(link)

        except:
            continue

    return all_data

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="Web Scraper", layout="wide")

st.title("🌐 Web Scraper App")

url = st.text_input("Enter Website URL")
max_pages = st.slider("Number of pages to crawl", 1, 20, 5)

if st.button("Start Scraping"):
    if url:
        with st.spinner("Scraping in progress..."):
            data = crawl_website(url, max_pages)

            if data:
                df = pd.DataFrame(data)

                # Clean + remove duplicates
                df = df.fillna("")
                df = df.drop_duplicates()

                st.success("Scraping Completed ✅")

                st.dataframe(df, use_container_width=True)

                # CSV download
                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="scraped_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data found.")

    else:
        st.error("Please enter a valid URL")
