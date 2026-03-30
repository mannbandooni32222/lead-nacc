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
    "User-Agent": "Mozilla/5.0"
}

# -------------------------------
# HELPERS
# -------------------------------
def extract_username(url):
    try:
        path = urlparse(url).path.strip("/")
        return path.split("/")[0]
    except:
        return ""

def scrape_page(url):
    results = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()

        emails = list(set(re.findall(EMAIL_REGEX, text)))
        phones = list(set(re.findall(PHONE_REGEX, text)))

        links = [a.get("href") for a in soup.find_all("a", href=True)]

        social_links = []
        usernames = []

        for link in links:
            full_link = urljoin(url, link)

            if any(domain in full_link for domain in SOCIAL_DOMAINS):
                social_links.append(full_link)
                usernames.append(extract_username(full_link))

        results.append({
            "Website": url,
            "Emails": ", ".join(emails),
            "Phones": ", ".join(phones),
            "Social Links": ", ".join(set(social_links)),
            "Usernames": ", ".join(set(usernames))
        })

    except Exception as e:
        results.append({
            "Website": url,
            "Emails": "",
            "Phones": "",
            "Social Links": "",
            "Usernames": "",
            "Error": str(e)
        })

    return results

def crawl_website(start_url, max_pages=3):
    visited = set()
    to_visit = [start_url]
    collected = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)

        if url in visited:
            continue

        visited.add(url)

        collected.extend(scrape_page(url))

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

    return collected

def bulk_scrape(url_list, max_pages):
    all_results = []

    for url in url_list:
        all_results.extend(crawl_website(url.strip(), max_pages))

    return all_results

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="Bulk Web Scraper", layout="wide")

st.title("🌐 Bulk Website Scraper")

st.markdown("Enter multiple URLs (one per line):")

url_input = st.text_area("Website URLs")

max_pages = st.slider("Pages per website", 1, 10, 3)

if st.button("Start Bulk Scraping"):
    if url_input.strip():
        urls = url_input.split("\n")

        with st.spinner("Scraping multiple websites..."):
            data = bulk_scrape(urls, max_pages)

            if data:
                df = pd.DataFrame(data)

                # Clean + deduplicate
                df = df.fillna("")
                df = df.drop_duplicates()

                st.success("Bulk Scraping Completed ✅")

                st.dataframe(df, use_container_width=True)

                # CSV Download
                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="bulk_scraped_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data found.")

    else:
        st.error("Please enter at least one URL")
