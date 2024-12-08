import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import asyncio
import re

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
        '/ara [ürün adı] - Trendyol, HB, N11 ve Amazon fiyatlarını karşılaştırır\n'
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
                products = soup.select('.prdct-desc-cntnr-ttl-w')[:3]
                prices = soup.select('.prc-box-dscntd')[:3]
                
                results = []
                for product, price in zip(products, prices):
                    name = product.text.strip()
                    price_text = price.text.strip()
                    results.append(f"{name}: {price_text}")
                return results
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
                products = soup.select('.product-card')[:3]
                results = []
                for product in products:
                    name = product.select_one('.product-card-name')
                    price = product.select_one('.price-value')
                    if name and price:
                        results.append(f"{name.text.strip()}: {price.text.strip()} TL")
                return results
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
                products = soup.select('.productName')[:3]
                prices = soup.select('.priceContainer .newPrice')[:3]
                
                results = []
                for product, price in zip(products, prices):
                    name = product.text.strip()
                    price_text = price.text.strip()
                    results.append(f"{name}: {price_text}")
                return results
    except Exception as e:
        logging.error(f"N11 error: {str(e)}")
    return []

async def fetch_amazon(session, product_name):
    try:
        url = f'https://www.amazon.com.tr/s?k={product_name}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.select('.s-result-item[data-component-type="s-search-result"]')[:3]
                
                results = []
                for product in products:
                    name = product.select_one('.a-text-normal')
                    price = product.select_one('.a-price .a-offscreen')
                    if name and price:
                        results.append(f"{name.text.strip()}: {price.text.strip()}")
                return results
    except Exception as e:
        logging.error(f"Amazon error: {str(e)}")
    return []

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Lütfen bir ürün adı girin. Örnek: /ara ütü masası')
        return

    product_name = ' '.join(context.args)
    await update.message.reply_text(f'🔍 {product_name} için fiyatlar karşılaştırılıyor...')

    async with aiohttp.ClientSession() as session:
        trendyol_results, hepsiburada_results, n11_results, amazon_results = await asyncio.gather(
            fetch_trendyol(session, product_name),
            fetch_hepsiburada(session, product_name),
            fetch_n11(session, product_name),
            fetch_amazon(session, product_name)
        )

        message = f'📊 {product_name} için bulunan ürünler:\n\n'
        
        if trendyol_results:
            message += '🛍️ Trendyol:\n'
            for result in trendyol_results:
                message += f'• {result}\n'
            message += '\n'
        
        if hepsiburada_results:
            message += '🛒 Hepsiburada:\n'
            for result in hepsiburada_results:
                message += f'• {result}\n'
            message += '\n'
        
        if n11_results:
            message += '🏪 N11:\n'
            for result in n11_results:
                message += f'• {result}\n'
            message += '\n'
            
        if amazon_results:
            message += '📦 Amazon:\n'
            for result in amazon_results:
                message += f'• {result}\n'
            message += '\n'

        if not any([trendyol_results, hepsiburada_results, n11_results, amazon_results]):
            message = '❌ Üzgünüm, ürün bulunamadı.'

        await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🔍 Komut Listesi:\n\n'
        '/ara [ürün adı] - Tüm sitelerdeki fiyatları karşılaştırır\n'
        '/yardim - Bu menüyü gösterir\n\n'
        '📝 Örnek Kullanım:\n'
        '/ara ütü masası\n\n'
        '🛒 Desteklenen Siteler:\n'
        '- Trendyol\n'
        '- Hepsiburada\n'
        '- N11\n'
        '- Amazon'
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ara", search_product))
    application.add_handler(CommandHandler("yardim", help_command))
    application.run_polling()

if __name__ == '__main__':
    main()