import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Merhaba! Ben fiyat karşılaştırma botuyum. 🤖\n'
        'Komutlar:\n'
        '/ara [ürün adı] - Trendyol, Hepsiburada ve N11 fiyatlarını karşılaştırır\n'
        '/yardim - Yardım menüsünü gösterir'
    )

async def fetch_trendyol(session, product_name):
    try:
        url = f'https://www.trendyol.com/sr?q={product_name}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('.prc-box-dscntd')
                return [price.text.strip() for price in products[:3]] if products else []
    except Exception as e:
        logging.error(f"Trendyol error: {str(e)}")
    return []

async def fetch_hepsiburada(session, product_name):
    try:
        url = f'https://www.hepsiburada.com/ara?q={product_name}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('.price-value')
                return [price.text.strip() for price in products[:3]] if products else []
    except Exception as e:
        logging.error(f"Hepsiburada error: {str(e)}")
    return []

async def fetch_n11(session, product_name):
    try:
        url = f'https://www.n11.com/arama?q={product_name}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('.newPrice')
                return [price.text.strip() for price in products[:3]] if products else []
    except Exception as e:
        logging.error(f"N11 error: {str(e)}")
    return []

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Lütfen bir ürün adı girin. Örnek: /ara ütü masası')
        return

    product_name = ' '.join(context.args)
    await update.message.reply_text(f'🔍 {product_name} için fiyatlar karşılaştırılıyor...')

    async with aiohttp.ClientSession() as session:
        # Paralel arama yapalım
        trendyol_prices, hepsiburada_prices, n11_prices = await asyncio.gather(
            fetch_trendyol(session, product_name),
            fetch_hepsiburada(session, product_name),
            fetch_n11(session, product_name)
        )

        message = f'📊 {product_name} için bulunan en düşük fiyatlar:\n\n'
        
        if trendyol_prices:
            message += '🛍️ Trendyol:\n'
            for i, price in enumerate(trendyol_prices, 1):
                message += f'{i}. {price}\n'
        
        if hepsiburada_prices:
            message += '\n🛒 Hepsiburada:\n'
            for i, price in enumerate(hepsiburada_prices, 1):
                message += f'{i}. {price}\n'
        
        if n11_prices:
            message += '\n🏪 N11:\n'
            for i, price in enumerate(n11_prices, 1):
                message += f'{i}. {price}\n'

        if not any([trendyol_prices, hepsiburada_prices, n11_prices]):
            message = '❌ Üzgünüm, ürün bulunamadı.'

        await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🔍 Komut Listesi:\n\n'
        '/ara [ürün adı] - Trendyol, Hepsiburada ve N11 fiyatlarını karşılaştırır\n'
        '/yardim - Bu menüyü gösterir\n\n'
        '📝 Örnek Kullanım:\n'
        '/ara ütü masası\n\n'
        '🛒 Desteklenen Siteler:\n'
        '- Trendyol\n'
        '- Hepsiburada\n'
        '- N11'
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ara", search_product))
    application.add_handler(CommandHandler("yardim", help_command))
    application.run_polling()

if __name__ == '__main__':
    main()