
# Instagram Comment & Profile Scraper

This project consists of two Python scripts that work together to scrape data from Instagram. The first script, `comment.py`, collects Instagram post URLs from a specified hashtag and extracts the usernames of users who commented on those posts, saving them to a CSV file (`comments.csv`). The second script, `phone2.py` (or `bio.py`), reads the usernames from `comments.csv`, retrieves each user’s profile information from Instagram (including biography), and then extracts contact details (phone number, email, and links) from the biography. The final output is saved into `profiles_phone.csv`.

## Files Description

- **comment.py**  
  **Functionality**:  
  - Opens Instagram’s hashtag page (e.g., for “保健品” or any other hashtag you specify) using Selenium.  
  - Scrolls down to load more posts and extracts each post’s basic URL (only the main post URL, excluding “liked_by” or “comments” URL variants).  
  - For each post, calls Instagram’s GraphQL API (using a fixed query hash) via httpx to fetch detailed post data (including comment information).  
  - Extracts the usernames from the comments and saves them as pairs of (post URL, comment username) in `comments.csv`.  

  **Requirements**:  
  - Python 3.x  
  - Selenium  
  - httpx  
  - Chrome browser and the corresponding ChromeDriver  
  - You must modify the code’s `user-data-dir` and `--profile-directory` parameters to match your own Chrome profile path.  
  - On the first run, if the browser navigates to a login page, you need to log in manually and then press Enter in the terminal to continue.

- **phone2.py** (or similarly named, e.g., bio.py)  
  **Functionality**:  
  - Reads the usernames collected in `comments.csv`.  
  - For each username, uses httpx to call Instagram’s user profile API endpoint (`https://i.instagram.com/api/v1/users/web_profile_info/?username={username}`) to retrieve profile data (which includes the biography).  
  - Uses regular expressions to extract contact details from the biography: phone number, email, and any links.  
  - Saves the final results (username, biography, phone number, email, and link) to `profiles_phone.csv`.

  **Requirements**:  
  - Python 3.x  
  - httpx  
  - The standard Python libraries (csv, re, json, time, random, urllib)  
  - If you want to maintain a logged-in state, update the `cookies` dictionary in the code with valid login cookies; otherwise, the API might return errors or limited data.

## Installation

Before running the scripts, install the required Python packages:

```bash
pip install selenium httpx
```

Also, download the ChromeDriver that matches your local Chrome version and ensure it is in your system PATH or specify its path in the code if necessary.

## How to Use

### 1. Run `comment.py` to Collect Comment Usernames

This script will:
- Open the specified hashtag page on Instagram.
- Scroll down to load more posts.
- Extract basic post URLs.
- For each post, fetch detailed post data via the GraphQL API.
- Extract the usernames of users who commented.
- Save the collected data to `comments.csv`.

**Run the script:**

```bash
python3 comment.py
```

**Notes:**
- If you encounter a login page, log in manually using the opened browser window and then press Enter in the terminal to continue.
- Modify the `user-data-dir` and `--profile-directory` parameters in the code to match your local Chrome profile settings.

### 2. Run `phone2.py` to Extract Profile Contact Details

This script will:
- Read the usernames from `comments.csv`.
- For each username, call the Instagram user profile API to retrieve profile information.
- Use regular expressions to extract the phone number, email, and link from the user's biography.
- Save the final profile information to `profiles_phone.csv`.

**Run the script:**

```bash
python3 phone2.py
```

**Notes:**
- To maintain a logged-in state, you should update the `cookies` dictionary in the script with valid cookie values (such as `sessionid`, `csrftoken`, etc.). Without valid cookies, the API may return an error or limited data.
- The scripts incorporate random delays between requests to help avoid being rate-limited by Instagram.

## Additional Notes

- **Login State & Cookies**:  
  Ensure you use a Chrome profile that is logged in to Instagram. You can obtain your login cookies via Selenium or manually copy them from your browser's developer tools.

- **Rate Limiting**:  
  Instagram has strict rate limits. If you receive messages such as “Please wait a few minutes before you try again,” you may need to increase the delay between requests or use proxies to distribute the requests.

- **Customization**:  
  Feel free to adjust the regular expressions used to extract phone numbers, emails, and links based on the actual format you observe in user biographies.
