import time
import random
import re
import json
import csv
from urllib.parse import quote

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------
# Constants
# ---------------------------
INSTAGRAM_QUERY_HASH = "97b41c52301f77ce508f55e66d17620e"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0",
]

def get_random_user_agent() -> str:
    """Return a random User-Agent string from our short list."""
    return random.choice(USER_AGENTS)

# ---------------------------
# Selenium-based Functions
# ---------------------------

def get_hashtag_posts(hashtag: str, scroll_times=2):
    """
    Use Selenium to open the hashtag page, scroll a bit,
    and collect up to `scroll_times` worth of post URLs.
    """
    encoded_hashtag = quote(hashtag)
    url = f"https://www.instagram.com/explore/tags/{encoded_hashtag}/"

    options = Options()
    # If you want to run headless, uncomment:
    # options.add_argument("--headless")
    
    # Adjust these paths for your Chrome profile if desired
    #options.add_argument("user-data-dir=/Users/xuhuirong/Library/Application Support/Google/Chrome")
    #options.add_argument("--profile-directory=Person 2")

    #print(f"[INFO] Launching Chrome to open hashtag page: {url}")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print("[INFO] Waiting for user to be logged in (if needed).")

    # If user is not logged in, manually log in
    while "accounts/login" in driver.current_url:
        print("[INFO] Login page detected, please log in manually in the opened browser.")
        input("[PROMPT] After logging in, press Enter here to continue...")
        time.sleep(3)

    # Wait until at least one post link is found
    try:
        print("[INFO] Waiting up to 60s for the first post to appear...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/p/']"))
        )
        print("[INFO] Found at least one post link.")
    except Exception as e:
        print("Hashtag page timed out or structure unexpected:", e)
        driver.quit()
        return []

    # Scroll down to load more posts
    print(f"[INFO] Scrolling the page {scroll_times} times to load more posts.")
    for i in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"[INFO] Scroll iteration {i+1} completed.")
        time.sleep(3)

    # Collect distinct post URLs
    print("[INFO] Collecting post URLs from the page.")
    post_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
    post_urls = set()
    for elem in post_elements:
        href = elem.get_attribute("href")
        if href and "/p/" in href and "liked_by" not in href and "comments" not in href:
            shortcode = href.split("/p/")[-1].split("/")[0]
            base_url = f"https://www.instagram.com/p/{shortcode}/"
            post_urls.add(base_url)

    driver.quit()
    print(f"[INFO] Total distinct post URLs found: {len(post_urls)}")
    return list(post_urls)


def get_cookies_from_driver():
    """
    Spin up a Selenium session on instagram.com, allowing for manual login if needed,
    then return the cookie dict for usage with httpx.
    """
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("user-data-dir=/Users/xuhuirong/Library/Application Support/Google/Chrome")
    options.add_argument("--profile-directory=Person 2")

    print("[INFO] Launching Chrome to retrieve cookies.")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.instagram.com")
    time.sleep(5)

    while "accounts/login" in driver.current_url:
        print("[INFO] Login page detected, please log in manually.")
        input("[PROMPT] Press Enter after logging in...")
        time.sleep(3)

    selenium_cookies = driver.get_cookies()
    cookie_dict = {}
    for cookie in selenium_cookies:
        cookie_dict[cookie["name"]] = cookie["value"]

    driver.quit()
    print(f"[INFO] Retrieved {len(cookie_dict)} cookies.")
    return cookie_dict

# ---------------------------
# Post & Comment Scraping
# ---------------------------

def scrape_post(url_or_shortcode: str, cookies: dict) -> dict:
    """
    Calls Instagram GraphQL to retrieve JSON about the post (including comments).
    """
    if "http" in url_or_shortcode:
        shortcode = url_or_shortcode.split("/p/")[-1].split("/")[0]
    else:
        shortcode = url_or_shortcode

    print(f"[INFO] Scraping post shortcode: {shortcode}")

    variables = json.dumps({
        "shortcode": shortcode,
        "first": 50,  # how many comments to retrieve
        "after": None
    }, separators=(',', ':'))

    body = f"query_hash={INSTAGRAM_QUERY_HASH}&variables={quote(variables)}"
    graphql_url = "https://www.instagram.com/graphql/query"

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "User-Agent": get_random_user_agent()
    }

    try:
        response = httpx.post(
            url=graphql_url,
            headers=headers,
            data=body,
            cookies=cookies,
            timeout=60.0
        )
        print(f"[INFO] Received status code: {response.status_code}")
        # For debug, you could show part of the response text, but it's often large:
        # print("Response text:", response.text)

        data = response.json()
        return data["data"]["shortcode_media"]
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for post {shortcode}: {e}")
        return {}

def extract_comment_usernames(post_json: dict) -> list:
    """
    Extracts commenters' usernames from a post's JSON data.
    """
    usernames = []
    comment_data = None
    if "edge_media_to_parent_comment" in post_json:
        comment_data = post_json["edge_media_to_parent_comment"]
    elif "edge_media_to_comment" in post_json:
        comment_data = post_json["edge_media_to_comment"]

    if comment_data:
        for edge in comment_data.get("edges", []):
            node = edge.get("node", {})
            owner = node.get("owner", {})
            username = owner.get("username")
            if username and username not in usernames:
                usernames.append(username)

    print(f"[INFO] Found {len(usernames)} unique commenter usernames in post data.")
    return usernames

# ---------------------------
# Profile Scraping
# ---------------------------

def get_user_profile(username: str, client: httpx.Client, cookies: dict = None) -> dict:
    """
    Calls the Instagram web_profile_info endpoint to get user biography, etc.
    """
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": get_random_user_agent(),
        "x-ig-app-id": "936619743392459",
        "Accept": "application/json",
        "Referer": "https://www.instagram.com/"
    }
    retries = 3
    for attempt in range(retries):
        try:
            print(f"[INFO] Attempt {attempt+1}: Fetching profile for user '{username}'")
            response = client.get(url, headers=headers, cookies=cookies, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("user", {})
            else:
                print(f"[WARN] [{username}] Non-200 status code: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] [{username}] Error fetching info (attempt {attempt + 1}): {e}")
        sleep_time = 2 + random.random() * 2
        print(f"[INFO] Waiting {sleep_time:.1f} seconds before retrying user {username}...")
        time.sleep(sleep_time)
    return {}

def extract_phone_from_bio(bio: str) -> str:
    phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
    matches = phone_pattern.findall(bio)
    return matches[0] if matches else ""

def extract_email_from_bio(bio: str) -> str:
    email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    matches = email_pattern.findall(bio)
    return matches[0] if matches else ""

def extract_link_from_bio(bio: str) -> str:
    link_pattern = re.compile(r'https?://[^\s]+')
    matches = link_pattern.findall(bio)
    return matches[0] if matches else ""
