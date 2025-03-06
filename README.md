
# Instagram 评论及用户简介爬虫

本项目包含两个 Python 脚本，用于采集 Instagram 指定标签下帖子的评论者用户名，并进一步获取这些用户的主页简介和联系信息（如电话号码、Email、链接等）。

## 文件说明

- **comment.py**  
  - **功能**：  
    1. 使用 Selenium 打开指定标签（例如“保健品”）的 Instagram 页面，滚动加载并提取帖子的基础链接。  
    2. 通过 Instagram GraphQL 接口获取每个帖子的详细数据（包括评论信息）。  
    3. 从每个帖子的 JSON 数据中提取评论者的用户名，并将结果保存到 `comments.csv` 文件中。  
  - **运行要求**：  
    - Python 3.x  
    - Selenium  
    - httpx  
    - Chrome 浏览器及对应版本的 ChromeDriver  
    - 修改代码中的 `user-data-dir` 和 `--profile-directory` 参数（根据你本地 Chrome 的用户数据路径）  
    - 在首次运行时，如果页面出现登录提示，需要手动登录后按回车继续。

- **phone2.py**（或你自己的文件名，例如 bio.py）  
  - **功能**：  
    1. 从上一步生成的 `comments.csv` 文件中读取评论中提到的用户名。  
    2. 使用 httpx 调用 Instagram 用户信息接口获取每个用户的详细信息（包括主页简介 biography）。  
    3. 从简介中提取联系信息：电话号码、Email 和链接。  
    4. 将最终结果保存到 `profiles_phone.csv` 文件中。  
  - **运行要求**：  
    - Python 3.x  
    - httpx  
    - 正则表达式模块（Python 标准库中自带）  
    - 如需保持登录状态，请在代码中配置有效的 Cookie 信息（修改 `cookies` 字典中的内容）；如果不配置，则接口将以匿名状态请求，可能返回错误信息或受限数据。

## 安装依赖

请确保你已经安装以下依赖库：

```bash
pip install selenium httpx
```

另外，请下载与你的 Chrome 版本相匹配的 ChromeDriver，并确保它在系统 PATH 中，或在代码中指定正确路径。

## 使用说明

### 1. 获取评论者用户名

首先运行 `comment.py` 脚本，该脚本会：
- 打开指定标签（在代码中可修改变量 `hashtag`）的 Instagram 页面。
- 滚动加载并提取帖子的基础链接。
- 对每个帖子调用 Instagram GraphQL 接口，提取评论中的用户名，并保存到 `comments.csv` 文件中。

运行方法：

```bash
python3 comment.py
```

注意：
- 如果第一次运行时出现登录页面，请在弹出的浏览器中手动登录 Instagram，然后回到终端按回车继续。
- 根据需要修改代码中 `user-data-dir` 和 `--profile-directory` 参数为你自己的 Chrome 用户数据路径及对应的 Profile 文件夹名称。

### 2. 获取用户简介和联系信息

运行 `phone2.py`，该脚本会：
- 从 `comments.csv` 中读取评论中提到的用户名（确保文件与脚本在同一目录）。
- 对每个用户名调用 Instagram 用户信息接口获取主页数据。
- 使用正则表达式从主页简介中提取电话号码、Email 以及链接。
- 最终将这些信息保存到 `profiles_phone.csv` 文件中。

运行方法：

```bash
python3 phone2.py
```

注意：
- 如需保持登录状态，请在代码中修改 `cookies` 字典（例如添加有效的 `sessionid` 等 Cookie 信息）；如果不使用 Cookie，则请求可能返回错误或受限信息。
- 请求之间有随机延时，防止请求过快导致被限流。

## 注意事项

- **登录状态**：  
  建议在 Selenium 中使用你自己的 Chrome 用户数据（`user-data-dir` 和 `--profile-directory`）以保持登录状态。如果运行时出现登录提示，请手动登录后再继续。

- **请求频率**：  
  Instagram 对请求频率有较严格的限制。如果出现限流提示（例如 "Please wait a few minutes before you try again."），建议延长等待时间或者分批处理请求。

- **Cookie 配置**：  
  若你需要接口返回更多数据（例如用户简介、联系方式），请确保在 `phone2.py` 中配置有效的登录状态 Cookie。你可以通过 Selenium 获取后传入，或手动复制粘贴。

- **ChromeDriver 版本**：  
  请确保下载与你本地 Chrome 浏览器版本匹配的 ChromeDriver。
