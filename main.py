import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import asyncio
import sys

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def shutdown():
    """Properly shutdown the bot"""
    logger.info("Shutting down...")
    sys.exit(0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Merhaba! Ben fiyat karşılaştırma botuyum. 🤖\n'
        'Komutlar:\n'
        '/ara [ürün adı] - Tüm sitelerdeki fiyatları karşılaştırır\n'
        '/yardim - Yardım menüsünü gösterir'
    )

async def fetch_prices(session, url, headers, selectors):
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                results = []
                for selector in selectors:
                    elements = soup.select(selector)
                    for elem in elements[:3]:
                        results.append(elem.text.strip())
                return results
    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
    return []

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Lütfen bir ürün adı girin. Örnek: /ara telefon')
        return

    product_name = ' '.join(context.args)
    await update.message.reply_text(f'🔍 "{product_name}" için fiyatlar aranıyor...')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    sites = {
        'Trendyol': {
            'url': f'https://www.trendyol.com/sr?q={product_name}',
            'selectors': ['.prdct-desc-cntnr-name', '.prc-box-dscntd']
        },
        'Hepsiburada': {
            'url': f'https://www.hepsiburada.com/ara?q={product_name}',
            'selectors': ['.product-name', '.price']
        },
        'Amazon': {
            'url': f'https://www.amazon.com.tr/s?k={product_name}',
            'selectors': ['.a-text-normal', '.a-price-whole']
        }
    }

    async with aiohttp.ClientSession() as session:
        results = {}
        for site_name, site_info in sites.items():
            prices = await fetch_prices(session, site_info['url'], headers, site_info['selectors'])
            if prices:
                results[site_name] = prices

        if results:
            message = f'📊 "{product_name}" için bulunan fiyatlar:\n\n'
            for site_name, prices in results.items():
                message += f'🏪 {site_name}:\n'
                for price in prices:
                    message += f'• {price}\n'
                message += '\n'
        else:
            message = '❌ Üzgünüm, ürün bulunamadı.'

        await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🔍 Komut Listesi:\n\n'
        '/ara [ürün adı] - Fiyatları karşılaştırır\n'
        '/yardim - Bu menüyü gösterir\n\n'
        '📝 Örnek Kullanım:\n'
        '/ara telefon\n\n'
        '🛒 Desteklenen Siteler:\n'
        '- Trendyol\n'
        '- Hepsiburada\n'
        '- Amazon'
    )

def main():
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("ara", search_product))
        app.add_handler(CommandHandler("yardim", help_command))
        
        logger.info("Bot started...")
        app.run_polling(stop_signals=None)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        shutdown()

if __name__ == '__main__':
    main()