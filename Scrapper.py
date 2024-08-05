import streamlit as st
from bs4 import BeautifulSoup
import requests
import urllib.parse
from collections import deque
import re
import os
import pandas as pd

# Create a folder in the user's home directory to store CSV files
output_dir = os.path.join(os.path.expanduser("~"), "scraped_emails")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def process_url(url):
    urls = deque([url])
    scraped_urls = set()
    emails = set()
    count = 0

    while len(urls):
        count += 1
        if count == 100:
            break
        url = urls.popleft()
        scraped_urls.add(url)

        parts = urllib.parse.urlsplit(url)
        base_url = '{0.scheme}://{0.netloc}'.format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url

        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            continue

        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
        emails.update(new_emails)

        soup = BeautifulSoup(response.text, 'html.parser')

        for anchor in soup.find_all("a"):
            link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            if link not in urls and link not in scraped_urls:
                urls.append(link)
    
    return emails, parts.netloc

st.title("Email Scraper")

urls_input = st.text_area("Enter Target URLs (one per line):")
if st.button("Submit"):
    urls = urls_input.split('\n')
    for url in urls:
        if url.strip():
            st.write(f"Processing {url.strip()} ...")
            emails, netloc = process_url(url.strip())
            if emails:
                df = pd.DataFrame(list(emails), columns=["Email"])
                csv_path = os.path.join(output_dir, f"{netloc}.csv")
                df.to_csv(csv_path, index=False)
                st.write(f"Emails from {url.strip()} saved to {csv_path}")
            else:
                st.write(f"No emails found on {url.strip()}")
