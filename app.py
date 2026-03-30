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

def classify_social_link(link):
    link_lower = link.lower()

    if "instagram.com" in link_lower:
        return "Instagram"
    elif "facebook.com" in link_lower:
        return "Facebook"
    elif "twitter.com" in link_lower or "x.com" in link_lower:
        return "X"
    elif "linkedin.com" in link_lower:
        return "LinkedIn"
    return None

def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()

        emails = list(set(re.findall(EMAIL_REGEX, text)))
        phones = list(set(re.findall(PHONE_REGEX, text)))

        links = [a.get("href") for a in soup.find_all("a", href=True)]

        instagram_links = set()
        facebook_links = set()
        x_links = set()
        linkedin_links = set()

        instagram_users = set()
        facebook_users = set()
        x_users = set()
        linkedin_users = set()

        for link in links:
            full_link = urljoin(url, link)
            platform = classify_social_link(full_link)

            if platform == "Instagram":
                instagram_links.add(full_link)
                instagram_users.add(extract_username(full_link))

            elif platform == "Facebook":
                facebook_links.add(full_link)
                facebook_users.add(extract_username(full_link))

            elif platform == "X":
                x_links.add(full_link)
                x_users.add(extract_username(full_link))

            elif platform == "LinkedIn":
                linkedin_links.add(full_link)
                linkedin_users.add(extract_username(full_link))

        return [{
            "Website": url,
            "Emails": ", ".join(emails),
            "Phones": ", ".join(phones),

            "Instagram Links": ", ".join(instagram_links),
            "Instagram Usernames": ", ".join(instagram_users),

            "Facebook Links": ", ".join(facebook_links),
            "Facebook Usernames": ", ".join(facebook_users),

            "X Links": ", ".join(x_links),
            "X Usernames": ", ".join(x_users),

            "LinkedIn Links": ", ".join(linkedin_links),
            "LinkedIn Usernames": ", ".join(linkedin_users),
        }]

    except Exception as e:
        return [{
            "Website": url,
            "Emails": "",
            "Phones": "",
            "Instagram Links": "",
            "Facebook Links": "",
            "X Links": "",
            "LinkedIn Links": "",
            "Error": str(e)
        }]

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
        if url.strip():
            all_results.extend(crawl_website(url.strip(), max_pages))

    return all_results

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.set_page_config(page_title="Bulk Web Scraper", layout="wide")

st.title("🌐 Bulk Website Scraper (Structured Social Data)")

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
