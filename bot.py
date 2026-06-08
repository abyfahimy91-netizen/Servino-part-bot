import os
import asyncio
from torob_integration.api import Torob
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
torob = Torob()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 سلام! به ربات استعلام قیمت قطعات خودرو خوش اومدی.\n\n"
        "اسم قطعه‌ای که می‌خوای رو بفرست تا قیمت و فروشنده‌هاش رو از ترب برات بیارم.\n\n"
        "مثال: فیلتر روغن پراید"
    )

async def search_torob(query: str) -> str:
    try:
        results = torob.search(query, page=0)
        
        if not results or "results" not in results:
            return (
                f"❌ نتیجه‌ای برای «{query}» پیدا نشد.\n\n"
                f"پیشنهاد: اسم قطعه رو دقیق‌تر بنویس."
            )

        items = results["results"]
        if not items:
            return f"❌ نتیجه‌ای برای «{query}» پیدا نشد."

        result = f"🔍 نتایج جستجو برای: *{query}*\n"
        result += "━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items[:5], 1):
            name = item.get("name", "نامشخص")
            min_price = item.get("price1", None)
            max_price = item.get("price2", None)
            link = f"https://torob.com/p/{item.get('token', '')}"

            result += f"*{i}. {name[:60]}*\n"
            if min_price and max_price:
                result += f"💰 {format(min_price, ',')} تا {format(max_price, ',')} تومان\n"
            elif min_price:
                result += f"💰 از {format(min_price, ',')} تومان\n"
            result += f"🔗 [مشاهده فروشنده‌ها]({link})\n\n"

        result += "━━━━━━━━━━━━━━━\n"
        result += "⚡ داده‌ها از ترب.کام"
        return result

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
