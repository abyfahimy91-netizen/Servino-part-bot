import os
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
        search_url = f"https://torob.com/search/?query={requests.utils.quote(query)}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return "❌ خطا در اتصال به ترب. لطفاً دوباره امتحان کن."
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find product cards
        products = soup.find_all("a", class_="SearchResultItem_itemLink__UxDhj", limit=5)
        
        if not products:
            # Try alternative class names
            products = soup.find_all("div", attrs={"data-testid": "search-result-item"}, limit=5)
        
        if not products:
            return f"❌ نتیجه‌ای برای «{query}» پیدا نشد.\n\nپیشنهاد: اسم قطعه رو دقیق‌تر بنویس. مثلاً: فیلتر روغن پراید 131"

        result = f"🔍 نتایج جستجو برای: *{query}*\n"
        result += "━━━━━━━━━━━━━━━\n\n"
        
        found = False
        for i, product in enumerate(products[:5], 1):
            try:
                # Get product name
                name_elem = product.find("p", class_="SearchResultItem_productName__UVqAn")
                if not name_elem:
                    name_elem = product.find("h2")
                if not name_elem:
                    name_elem = product.find("p")
                
                name = name_elem.get_text(strip=True) if name_elem else "نامشخص"
                
                # Get price
                price_elem = product.find("span", class_="SearchResultItem_price__BhWNI")
                if not price_elem:
                    price_elem = product.find("span", class_=lambda x: x and "price" in x.lower() if x else False)
                
                price = price_elem.get_text(strip=True) if price_elem else "قیمت نامشخص"
                
                # Get link
                href = product.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://torob.com" + href
                
                if name != "نامشخص":
                    found = True
                    result += f"*{i}. {name}*\n"
                    result += f"💰 قیمت: {price} تومان\n"
                    if href:
                        result += f"🔗 [مشاهده فروشنده‌ها]({href})\n"
                    result += "\n"
                    
            except Exception:
                continue
        
        if not found:
            return f"❌ نتیجه‌ای برای «{query}» پیدا نشد.\n\nپیشنهاد: اسم قطعه رو دقیق‌تر بنویس."
        
        result += "━━━━━━━━━━━━━━━\n"
        result += "⚡ داده‌ها از ترب.کام"
        
        return result
        
    except requests.Timeout:
        return "⏱ ترب دیر جواب داد. دوباره امتحان کن."
    except Exception as e:
        return f"❌ خطای غیرمنتظره: {str(e)}"

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

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ ربات شروع به کار کرد...")
    app.run_polling()

if __name__ == "__main__":
    main()
