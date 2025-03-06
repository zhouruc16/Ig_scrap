import re
import csv
import json
import time
import random
import httpx
from urllib.parse import quote

# 随机选取一个 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0",
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def get_user_profile(username: str, client: httpx.Client, cookies: dict = None) -> dict:
    """
    调用 Instagram 接口获取用户信息。
    返回的数据中 "data" -> "user" 包含用户简介（biography）等信息。
    如果请求失败会重试 3 次。
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
                # 调试时可取消注释，观察返回的完整 JSON 数据
                # print(f"{username} 返回的数据：", json.dumps(data, indent=2, ensure_ascii=False))
                return data.get("data", {}).get("user", {})
            else:
                print(f"[{username}] 请求失败，状态码：{response.status_code}")
        except Exception as e:
            print(f"[{username}] 获取信息出错（尝试 {attempt + 1}）：{e}")
        sleep_time = 2 + random.random() * 2
        print(f"等待 {sleep_time:.1f} 秒后重试……")
        time.sleep(sleep_time)
    return {}

def extract_phone_from_bio(bio: str) -> str:
    """
    使用正则表达式从简介中匹配电话号码。
    匹配规则可根据实际情况调整。
    """
    phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
    matches = phone_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def extract_email_from_bio(bio: str) -> str:
    """
    使用正则表达式从简介中匹配 email 地址。
    """
    email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    matches = email_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def extract_link_from_bio(bio: str) -> str:
    """
    使用正则表达式从简介中匹配链接（URL）。
    """
    link_pattern = re.compile(r'https?://[^\s]+')
    matches = link_pattern.findall(bio)
    if matches:
        return matches[0]
    return ""

def read_usernames_from_csv(filename: str) -> set:
    """
    从 CSV 文件中读取评论中提到的用户名，
    假设 CSV 文件中包含 "comment_username" 这一列，
    返回去重后的用户名集合。
    """
    usernames = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "comment_username" in row and row["comment_username"]:
                    usernames.add(row["comment_username"].strip())
    except Exception as e:
        print(f"读取文件 {filename} 失败：{e}")
    return usernames

def write_profiles_to_csv(profiles: list, filename: str):
    """
    将获取到的用户信息保存到 CSV 文件中，
    包含 username、biography、phone_number、email 和 link 字段。
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
    input_csv = "comments.csv"   # 包含评论中提到用户名的 CSV 文件
    output_csv = "profiles_phone.csv"  # 输出用户信息（含电话号码、email 和 link）的 CSV 文件
    
    print("读取评论中提到的用户名……")
    usernames = read_usernames_from_csv(input_csv)
    print(f"共找到 {len(usernames)} 个唯一用户名。")
    
    profiles = []
    # 这里如果有登录状态 Cookie，可填入有效的 Cookie 字典，否则设置为 None
    cookies = None
    
    with httpx.Client() as client:
        for username in usernames:
            print(f"开始获取用户 {username} 的信息……")
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
            print(f"请求完成，等待 {wait_time:.1f} 秒……")
            time.sleep(wait_time)
    
    write_profiles_to_csv(profiles, output_csv)
    print(f"用户信息已保存到 {output_csv}")

if __name__ == "__main__":
    main()
