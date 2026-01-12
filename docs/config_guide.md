# 🛠️ Siren 机器人配置指南

本指南将协助你从零开始配置并运行 Siren 机器人。

## 1. 获取 Discord Bot Token

1.  访问 [Discord Developer Portal](https://discord.com/developers/applications)。
2.  点击 **"New Application"**，输入名称（如 Siren）。
3.  在左侧菜单点击 **"Bot"**。
4.  点击 **"Reset Token"** 并复制生成的 Token。
5.  **重要**: 在下方 **"Privileged Gateway Intents"** 中开启：
    - `PRESENCE INTENT`
    - `SERVER MEMBERS INTENT`
    - `MESSAGE CONTENT INTENT` (必须开启，否则无法响应指令)
6.  保存更改。

## 2. 邀请机器人到服务器

1.  在左侧菜单点击 **"OAuth2"** -> **"URL Generator"**。
2.  在 **Scopes** 中勾选 `bot` 和 `applications.commands`。
3.  在 **Bot Permissions** 中勾选：
    - `Administrator` (省事之选) 或
    - `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`。
4.  复制生成的 URL 并粘贴到浏览器，选择你的服务器进行授权。

## 3. 获取频道 ID

1.  在 Discord 客户端中，打开 **"设置" (Settings)** -> **"高级" (Advanced)**。
2.  开启 **"开发者模式" (Developer Mode)**。
3.  回到服务器，右键点击你想接收通知的频道，选择 **"复制 ID" (Copy ID)**。

## 4. 填写配置文件

在 `Siren` 根目录下创建 `.env` 文件（或修改 `.env.example`）：

```env
DISCORD_TOKEN=你的机器人Token
DISCORD_CHANNEL_ID=你的频道ID
CHECK_INTERVAL=15
PING_EVERYONE=false
```

## 5. 部署说明

### 本地运行
```bash
pip install -r requirements.txt
python bot.py
```

### Docker 运行
```bash
docker build -t siren .
docker run -d --env-file .env siren
```
