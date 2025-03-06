import re
import csv
import json
import time
import random
import httpx
from urllib.parse import quote

# Randomly select a User-Agent from the list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0",
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def get_user_profile(username: str, client: httpx.Client, cookies: dict = None) -> dict:
    """
    Calls the Instagram API to get user information.
    The returned data's "data" -> "user" contains the user's biography and other info.
    If the request fails, it will retry 3 times.
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
            response = client.get(url, headers=headers, cookies=cookies, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                # Uncomment the following line during debugging to view the complete JSON data returned
                # print(f"{username} returned data:", json.dumps(data, indent=2, ensure_ascii=False))
                return data.get("data", {}).get("user", {})
            else:
                print(f"[{username}] Request failed, status code: {response.status_code}")
        except Exception as e:
            print(f"[{username}] Error fetching information (attempt {attempt + 1}): {e}")
        sleep_time = 2 + random.random() * 2
        print(f"Waiting {sleep_time:.1f} seconds before retrying...")
        time.sleep(sleep_time)
    return {}

def extract_phone_from_bio(bio: str) -> str:
    """
    Uses a regular expression to match a phone number from the biography.
    The matching pattern can be adjusted according to actual needs.
    """
    phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
    matches = phone_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def extract_email_from_bio(bio: str) -> str:
    """
    Uses a regular expression to match an email address from the biography.
    """
    email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    matches = email_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def extract_link_from_bio(bio: str) -> str:
    """
    Uses a regular expression to match a link (URL) from the biography.
    """
    link_pattern = re.compile(r'https?://[^\s]+')
    matches = link_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def read_usernames_from_csv(filename: str) -> set:
    """
    Reads the usernames mentioned in comments from a CSV file.
    Assumes the CSV file contains a column named "comment_username".
    Returns a set of unique usernames.
    """
    usernames = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "comment_username" in row and row["comment_username"]:
                    usernames.add(row["comment_username"].strip())
    except Exception as e:
        print(f"Failed to read file {filename}: {e}")
    return usernames

def write_profiles_to_csv(profiles: list, filename: str):
    """
    Saves the obtained user information to a CSV file,
    including the fields: username, biography, phone_number, email, and link.
    """
    with open(filename, "w", newline='', encoding="utf-8") as f:
        fieldnames = ["username", "biography", "phone_number", "email", "link"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for profile in profiles:
            writer.writerow({
                "username": profile.get("username", ""),
                "biography": profile.get("biography", ""),
                "phone_number": profile.get("phone_number", ""),
                "email": profile.get("email", ""),
                "link": profile.get("link", "")
            })

def main():
    input_csv = "comments.csv"   # CSV file that contains the usernames mentioned in comments
    output_csv = "profiles_phone.csv"  # CSV file to output user information (with phone number, email, and link)
    
    print("Reading usernames mentioned in comments...")
    usernames = read_usernames_from_csv(input_csv)
    print(f"Found {len(usernames)} unique usernames.")
    
    profiles = []
    # If you have a login state Cookie, you can pass a valid Cookie dictionary; otherwise, set it to None
    cookies = None
    
    with httpx.Client() as client:
        for username in usernames:
            print(f"Starting to fetch information for user {username}...")
            profile = get_user_profile(username, client, cookies)
            if profile:
                bio = profile.get("biography", "")
                phone = extract_phone_from_bio(bio)
                email = extract_email_from_bio(bio)
                link = extract_link_from_bio(bio)
                profile["phone_number"] = phone
                profile["email"] = email
                profile["link"] = link
                profiles.append(profile)
            wait_time = random.uniform(30, 60)
            print(f"Request completed, waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
    
    write_profiles_to_csv(profiles, output_csv)
    print(f"User information saved to {output_csv}")

if __name__ == "__main__":
    main()
