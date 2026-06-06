import os
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 سلام! به ربات استعلام قیمت قطعات خودرو خوش اومدی.\n\n"
        "اسم قطعه‌ای که می‌خوای رو بفرست تا قیمت و فروشنده‌هاش رو از ترب برات بیارم.\n\n"
        "مثال: فیلتر روغن پراید"
    )

async def search_torob(query: str) -> str:
    try:
        encoded = requests.utils.quote(query)
        search_url = f"https://torob.com/search/?query={encoded}"
        response = requests.get(search_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return "❌ خطا در اتصال به ترب. لطفاً دوباره امتحان کن."

        soup = BeautifulSoup(response.text, "html.parser")
        all_links = soup.find_all("a", href=True)
        product_links = [a for a in all_links if "/p/" in a.get("href", "")]

        if not product_links:
            return (
                f"❌ نتیجه‌ای برای «{query}» پیدا نشد.\n\n"
                f"🔗 جستجوی مستقیم در ترب:\n"
                f"https://torob.com/search/?query={encoded}"
            )

        result = f"🔍 نتایج جستجو برای: *{query}*\n"
        result += "━━━━━━━━━━━━━━━\n\n"

        count = 0
        seen = set()
        for a in product_links:
            if count >= 5:
                break
            href = a.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            name = a.get_text(strip=True)
            if not name or len(name) < 3:
                p = a.find("p")
                name = p.get_text(strip=True) if p else ""
            if not name or len(name) < 3:
                continue

            price_text = ""
            price_span = a.find(lambda tag: tag.name in ["span", "div", "p"] and tag.string and any(c.isdigit() for c in tag.string))
            if price_span:
                price_text = price_span.get_text(strip=True)

            full_url = f"https://torob.com{href}" if not href.startswith("http") else href

            count += 1
            result += f"*{count}. {name[:60]}*\n"
            if price_text:
                result += f"💰 {price_text}\n"
            result += f"🔗 [مشاهده فروشنده‌ها]({full_url})\n\n"

        if count == 0:
            return (
                f"❌ نتیجه‌ای برای «{query}» پیدا نشد.\n\n"
                f"🔗 جستجوی مستقیم:\nhttps://torob.com/search/?query={encoded}"
            )

        result += "━━━━━━━━━━━━━━━\n"
        result += "⚡ داده‌ها از ترب.کام"
        return result

    except requests.Timeout:
        return "⏱ ترب دیر جواب داد. دوباره امتحان کن."
    except Exception as e:
        return f"❌ خطا: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if len(query) < 2:
        await update.message.reply_text("لطفاً اسم قطعه رو کامل‌تر بنویس.")
        return
    await update.message.reply_text("🔎 دارم توی ترب دنبالش می‌گردم...")
    result = await search_torob(query)
    await update.message.reply_text(
        result,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ ربات شروع به کار کرد...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
