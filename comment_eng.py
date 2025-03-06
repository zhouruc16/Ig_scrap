import time
import csv
import json
from urllib.parse import quote
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

INSTAGRAM_QUERY_HASH = "97b41c52301f77ce508f55e66d17620e"

def get_hashtag_posts(hashtag: str, scroll_times=2):
    # Encode the hashtag for use in a URL
    encoded_hashtag = quote(hashtag)
    url = f"https://www.instagram.com/explore/tags/{encoded_hashtag}/"
    
    options = Options()
    # Uncomment the following line to run in headless mode if desired:
    # options.add_argument("--headless")
    options.add_argument("user-data-dir=/Users/xuhuirong/Library/Application Support/Google/Chrome")
    options.add_argument("--profile-directory=Person 2")
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # If a login page is detected, prompt the user to log in manually and press Enter to continue...
    while "accounts/login" in driver.current_url:
        print("Login page detected, please log in manually in the opened browser and press Enter to continue...")
        input()
        time.sleep(3)
    
    try:
        # Wait up to 60 seconds until at least one post link is found on the page
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/p/']"))
        )
    except Exception as e:
        print("Hashtag page timed out or has an unexpected structure:", e)
        driver.quit()
        return []
    
    # Scroll down the page a few times to load more posts
    for _ in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
    
    # Find all elements containing post links
    post_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
    post_urls = set()
    for elem in post_elements:
        href = elem.get_attribute("href")
        # Filter out URLs that are not base post URLs (exclude those with "liked_by" or "comments")
        if href and "/p/" in href and "liked_by" not in href and "comments" not in href:
            shortcode = href.split("/p/")[-1].split("/")[0]
            base_url = f"https://www.instagram.com/p/{shortcode}/"
            post_urls.add(base_url)
    
    driver.quit()
    return list(post_urls)

def get_cookies_from_driver(driver) -> dict:
    # Retrieve cookies from Selenium and return as a dictionary
    selenium_cookies = driver.get_cookies()
    cookies = {}
    for cookie in selenium_cookies:
        cookies[cookie['name']] = cookie['value']
    return cookies

def scrape_post(url_or_shortcode: str, cookies: dict) -> dict:
    if "http" in url_or_shortcode:
        shortcode = url_or_shortcode.split("/p/")[-1].split("/")[0]
    else:
        shortcode = url_or_shortcode
    print(f"Scraping post: {shortcode}")
    
    # Prepare JSON variables for the GraphQL query
    variables = json.dumps({
        "shortcode": shortcode,
        "first": 50,
        "after": None
    }, separators=(',', ':'))
    body = f"query_hash={INSTAGRAM_QUERY_HASH}&variables={quote(variables)}"
    graphql_url = "https://www.instagram.com/graphql/query"
    
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    response = httpx.post(url=graphql_url, headers=headers, data=body, cookies=cookies, timeout=60.0)
    print("Response text:", response.text)  
    try:
        data = response.json()
        # Based on the current response structure, comment data is usually in data["shortcode_media"]["edge_media_to_comment"]
        return data["data"]["shortcode_media"]
    except Exception as e:
        print(f"Error parsing JSON for post {shortcode}: {e}")
        return {}

def extract_comment_usernames(post_json: dict) -> list:
    """
    Extract a list of comment usernames from the post JSON data.
    If the data contains 'edge_media_to_parent_comment', use it;
    otherwise, use 'edge_media_to_comment'.
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
    return usernames

def main():
    hashtag = "保健品"
    print(f"Fetching posts for #{hashtag}...")
    post_urls = get_hashtag_posts(hashtag, scroll_times=2)
    print(f"Found {len(post_urls)} posts for #{hashtag}.")
    
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("user-data-dir=/Users/xuhuirong/Library/Application Support/Google/Chrome")
    options.add_argument("--profile-directory=Person 2")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.instagram.com")
    time.sleep(5)
    cookies = get_cookies_from_driver(driver)
    driver.quit()
    
    results = []  # (post_url, comment_username)
    
    for post_url in post_urls:
        print(f"Processing post: {post_url}")
        post_json = scrape_post(post_url, cookies)
        if not post_json:
            print(f"Failed to get post data: {post_url}")
            continue
        usernames = extract_comment_usernames(post_json)
        if usernames:
            print(f"Found comment usernames: {usernames}")
            for username in usernames:
                results.append((post_url, username))
        else:
            print(f"No comments found for {post_url}.")
        time.sleep(2)
    
    csv_filename = "comments.csv"
    with open(csv_filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["post_url", "comment_username"])
        writer.writerows(results)
    
    print(f"Saved results to {csv_filename}")

if __name__ == "__main__":
    main()
