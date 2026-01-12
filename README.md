## 📖 项目文档
- [🛠️ 配置指南](docs/config_guide.md): 如何获取 Token 并启动机器人。
- [📖 使用手册](docs/usage_manual.md): 指令说明与功能介绍。

## 主要功能
- **定时爬取**: 自动检查 MissAV 最新视频。
- **Discord 推送**: 发现新片时，自动发送到指定频道。
- **机器人指令**:
  - `/subscribe`: 订阅全部/演员/标签。
  - `/unsubscribe`: 取消订阅。
  - `/list`: 管理我的订阅。
  - `/search`: 快速搜索视频。
  - `/latest`: 查看历史记录中的最新视频。
  - `/status`: 查看运行状态。
  - `/crawl_code`: 强制爬取特定番号。

## 环境要求
- Python 3.10+
- Discord Bot Token

## 快速开始

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**:
   复制 `.env.example` 并重命名为 `.env`，填写你的 Token 和频道 ID：
   ```env
   DISCORD_TOKEN=你的Token
   DISCORD_CHANNEL_ID=频道ID
   ```

3. **运行机器人**:
   ```bash
   python bot.py
   ```

## 目录结构
- `bot.py`: 机器人入口及指令逻辑。
- `crawler.py`: 异步爬虫逻辑。
- `database.py`: SQLite 数据存储逻辑。
- `data/`: 持久化数据目录（建议挂载卷）。
- `data/missav.db`: 自动生成的数据库文件。
