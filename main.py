import time
import random
import csv
import httpx

# Import all utility functions from utils.py
from utils import (
    get_hashtag_posts,
    get_cookies_from_driver,
    scrape_post,
    extract_comment_usernames,
    get_user_profile,
    extract_phone_from_bio,
    extract_email_from_bio,
    extract_link_from_bio
)


def main():
    # 1) User inputs: hashtag and number of posts
    hashtag = input("[PROMPT] Enter hashtag (e.g. 保健品): ").strip()
    max_posts = int(input("[PROMPT] Enter how many posts to scrape: "))

    # 2) Fetch up to max_posts post URLs
    print(f"[INFO] Fetching posts for #{hashtag} ...")
    all_posts = get_hashtag_posts(hashtag, scroll_times=2)
    if not all_posts:
        print("[INFO] No posts found. Exiting.")
        return

    # If we found more than max_posts, slice
    post_urls = all_posts[:max_posts]
    print(f"[INFO] We have {len(post_urls)} post URLs (limited to {max_posts}).")

    print("[INFO] Retrieving cookies so we can call GraphQL / web_profile_info")
    cookies = get_cookies_from_driver()

    # 4) Gather commenter usernames from each post
    post_to_usernames = {}  # { post_url: [username1, username2, ...] }
    with httpx.Client() as client:
        print(f"[INFO] Now scraping comment data from each of the {len(post_urls)} posts.")
        for i, post_url in enumerate(post_urls, start=1):
            print(f"[INFO] Processing post {i}/{len(post_urls)}: {post_url}")
            post_json = scrape_post(post_url, cookies)
            if not post_json:
                print(f"[WARN] Failed to get post data for {post_url}")
                continue
            commenters = extract_comment_usernames(post_json)
            post_to_usernames[post_url] = commenters
            time.sleep(2)

    # 5) For each commenter, get profile, extract phone/email/link, and write to CSV
    csv_filename = "profiles_phone.csv"
    print(f"[INFO] Writing profile data to {csv_filename}")
    with open(csv_filename, "w", newline='', encoding="utf-8") as f:
        fieldnames = ["post_url", "username", "biography", "phone_number", "email", "link"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with httpx.Client() as client:
            for post_url, usernames in post_to_usernames.items():
                print(f"[INFO] Found {len(usernames)} commenters for post: {post_url}")
                for username in usernames:
                    print(f"[INFO] Fetching user profile for {username}")
                    profile_data = get_user_profile(username, client, cookies)
                    if profile_data:
                        biography = profile_data.get("biography", "")
                        phone = extract_phone_from_bio(biography)
                        email = extract_email_from_bio(biography)
                        link = extract_link_from_bio(biography)

                        row = {
                            "post_url": post_url,
                            "username": username,
                            "biography": biography,
                            "phone_number": phone,
                            "email": email,
                            "link": link
                        }
                        writer.writerow(row)
                        f.flush()
                        print(f"[INFO] Wrote profile data for {username}.")
                    else:
                        print(f"[WARN] Could not retrieve profile data for {username}")

                    wait_time = random.uniform(30, 60)
                    print(f"[INFO] Done with {username}, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)

    print(f"[INFO] All done! Results saved to {csv_filename}")


if __name__ == "__main__":
    main()
