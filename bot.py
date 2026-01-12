import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import logging
from datetime import datetime

from database import Database
from crawler import MissavCrawler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

class SirenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.owner_ids = {1389282563121741904} # Set user as owner
        self.db = Database("data/missav.db")
        self.crawler = MissavCrawler()
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 15)) # Minutes

    async def setup_hook(self):
        await self.crawler.init_session()
        self.check_new_videos.start()
        await self.tree.sync()
        logger.info("Bot commands synced and background task started.")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')

    @tasks.loop(minutes=15)
    async def check_new_videos(self):
        logger.info("Checking for new videos...")
        new_videos = await self.crawler.crawl_new_videos(pages=1)
        for video in new_videos:
            if not self.db.is_video_exists(video['code']):
                # Fetch full detail for better notification
                detail = await self.crawler.crawl_video_detail(video['detail_url'])
                if detail:
                    video.update(detail)
                
                saved = self.db.save_video(video)
                if saved and CHANNEL_ID:
                    await self.push_video_to_channel(video)

    async def push_video_to_channel(self, video):
        channel = self.get_channel(CHANNEL_ID)
        if not channel: return
        
        embed = self.create_video_embed(video)
        await channel.send(content="@everyone 发现新片！" if os.getenv('PING_EVERYONE') == 'true' else None, embed=embed)

    def create_video_embed(self, video):
        embed = discord.Embed(
            title=video.get('title', 'Unknown Title'),
            url=video.get('detail_url'),
            color=discord.Color.blue()
        )
        embed.add_field(name="番号", value=video.get('code', 'N/A'), inline=True)
        embed.add_field(name="时长", value=f"{video.get('duration', 'N/A')} 分钟", inline=True)
        embed.add_field(name="演员", value=video.get('actresses', 'N/A'), inline=False)
        embed.add_field(name="标签", value=video.get('tags', 'N/A'), inline=False)
        embed.add_field(name="来源", value=video.get('source', 'Siren Internal'), inline=True)
        
        if video.get('cover_url'):
            embed.set_image(url=video.get('cover_url'))
            
        embed.set_footer(text=f"Siren 综合影视系统 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

bot = SirenBot()

@bot.command(name="siren-sync")
@commands.is_owner()
async def sync(ctx):
    """强制同步 Slash Commands (仅限 Bot 所有者)"""
    await ctx.send("🔄 正在强制同步 Slash Commands...")
    try:
        await bot.tree.sync()
        if ctx.guild:
            bot.tree.copy_global_to(guild=ctx.guild)
            await bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ 指令同步完成！请完全重启 Discord 客户端或稍候片刻。")
    except Exception as e:
        await ctx.send(f"❌ 同步失败: {e}")

@bot.tree.command(name="help", description="查看帮助信息")
async def help(interaction: discord.Interaction):
    help_text = """
🎬 **MissAV 机器人帮助**

📌 **订阅命令**
- `/subscribe` - 订阅全部新片
- `/subscribe_actress [name]` - 订阅指定演员
- `/subscribe_tag [tag]` - 订阅指定标签

📌 **管理命令**
- `/unsubscribe` - 取消全部订阅
- `/list` - 查看当前订阅

📌 **查询命令**
- `/search [keyword]` - 搜索视频
- `/latest [count]` - 查看最新视频
- `/status` - 机器人状态

📌 **手动爬取**
- `/crawl_actor [name] [limit]` - 手动爬取演员作品
- `/crawl_code [code]` - 手动爬取番号
- `/crawl_search [keyword] [limit]` - 手动搜索爬取
    """
    await interaction.response.send_message(help_text)

@bot.tree.command(name="latest", description="查看最新视频")
@app_commands.describe(count="显示的视频数量")
async def latest(interaction: discord.Interaction, count: int = 5):
    await interaction.response.defer()
    videos = bot.db.get_latest_videos(limit=count)
    if not videos:
        await interaction.followup.send("数据库中暂无视频记录。")
        return
        
    for video in videos:
        embed = bot.create_video_embed(video)
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="status", description="查看机器人状态")
async def status(interaction: discord.Interaction):
    crawler_count = len(bot.crawler.crawlers)
    status_text = f"🤖 **机器人状态**\n\n✅ 运行中\n📡 活跃数据源: {crawler_count} 个\n⏰ 检查频率: {bot.check_interval} 分钟"
    await interaction.response.send_message(status_text)

@bot.tree.command(name="search", description="全网搜索视频")
@app_commands.describe(keyword="关键词 (支持番号或名称)")
async def search(interaction: discord.Interaction, keyword: str):
    await interaction.response.defer()
    results = await bot.crawler.search(keyword, limit=5)
    
    if not results:
        await interaction.followup.send(f"🔍 全网未找到相关视频: {keyword}")
        return
        
    for v in results:
        embed = bot.create_video_embed(v)
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="crawl_code", description="手动爬取特定番号 (全网搜)")
@app_commands.describe(code="番号 (如 SSIS-001)")
async def crawl_code(interaction: discord.Interaction, code: str):
    await interaction.response.defer()
    video = await bot.crawler.crawl_video_detail(code) # Now it will search all sources
    if video:
        bot.db.save_video(video)
        embed = bot.create_video_embed(video)
        await interaction.followup.send(content="✅ 爬取成功！", embed=embed)
    else:
        await interaction.followup.send(f"❌ 未找到番号: {code}")

@bot.tree.command(name="subscribe", description="订阅全部新片")
async def subscribe(interaction: discord.Interaction):
    bot.db.subscribe(interaction.user.id, "USER", "ALL")
    await interaction.response.send_message("✅ 已开启全部新片订阅通知！")

@bot.tree.command(name="subscribe_actress", description="订阅指定演员")
@app_commands.describe(name="演员姓名")
async def subscribe_actress(interaction: discord.Interaction, name: str):
    bot.db.subscribe(interaction.user.id, "USER", "ACTRESS", name)
    await interaction.response.send_message(f"✅ 已订阅演员: {name}。有新作会立即通知你！")

@bot.tree.command(name="subscribe_tag", description="订阅指定标签")
@app_commands.describe(tag="标签名称")
async def subscribe_tag(interaction: discord.Interaction, tag: str):
    bot.db.subscribe(interaction.user.id, "USER", "TAG", tag)
    await interaction.response.send_message(f"✅ 已订阅标签: {tag}。有相关作品会立即通知你！")

@bot.tree.command(name="unsubscribe", description="取消全部订阅")
async def unsubscribe(interaction: discord.Interaction):
    bot.db.unsubscribe(interaction.user.id)
    await interaction.response.send_message("🔕 已取消所有订阅通知。")

@bot.tree.command(name="list", description="查看当前订阅")
async def list_subs(interaction: discord.Interaction):
    subs = bot.db.get_subscriptions(interaction.user.id)
    if not subs:
        await interaction.response.send_message("你目前还没有任何订阅。")
        return
    
    lines = ["📋 **你的订阅列表:**"]
    for s in subs:
        if s['type'] == 'ALL':
            lines.append("- 全部新片推送")
        else:
            lines.append(f"- {s['type']}: {s['keyword']}")
    
    await interaction.response.send_message("\n".join(lines))

@bot.tree.command(name="crawl_actor", description="手动爬取演员作品")
@app_commands.describe(name="演员姓名", limit="爬取数量 (默认 10)")
async def crawl_actor(interaction: discord.Interaction, name: str, limit: int = 10):
    await interaction.response.defer()
    results = await bot.crawler.search(name, limit=limit)
    if not results:
        await interaction.followup.send(f"❌ 未找到演员 {name} 的作品。")
        return
    
    count = 0
    for v in results:
        if not bot.db.is_video_exists(v['code']):
            detail = await bot.crawler.crawl_video_detail(v['detail_url'])
            if detail: v.update(detail)
            bot.db.save_video(v)
            count += 1
            
    await interaction.followup.send(f"✅ 爬取完成！共为演员 {name} 更新了 {count} 部作品。")

@bot.tree.command(name="crawl_search", description="手动搜索爬取")
@app_commands.describe(keyword="关键词", limit="爬取数量 (默认 10)")
async def crawl_search(interaction: discord.Interaction, keyword: str, limit: int = 10):
    await interaction.response.defer()
    results = await bot.crawler.search(keyword, limit=limit)
    if not results:
        await interaction.followup.send(f"❌ 未找到关键词 {keyword} 的相关视频。")
        return
    
    count = 0
    for v in results:
        if not bot.db.is_video_exists(v['code']):
            detail = await bot.crawler.crawl_video_detail(v['detail_url'])
            if detail: v.update(detail)
            bot.db.save_video(v)
            count += 1
            
    await interaction.followup.send(f"✅ 爬取完成！共为关键词 {keyword} 更新了 {count} 个视频。")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
