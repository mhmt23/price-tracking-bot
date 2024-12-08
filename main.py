import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Merhaba! Ben fiyat takip botuyum. 🤖\n'
        'Komutlar:\n'
        '/ara [ürün adı] - Ürün fiyatlarını arar\n'
        '/yardim - Yardım menüsünü gösterir'
    )

async def search_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for product prices."""
    if not context.args:
        await update.message.reply_text('Lütfen bir ürün adı girin. Örnek: /ara ütü masası')
        return

    product_name = ' '.join(context.args)
    await update.message.reply_text(f'🔍 {product_name} için arama yapılıyor...')

    try:
        # Trendyol search
        async with aiohttp.ClientSession() as session:
            url = f'https://www.trendyol.com/sr?q={product_name}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    products = soup.select('.prc-box-dscntd')  # Trendyol price selector
                    
                    if products:
                        message = f'📊 {product_name} için bulunan fiyatlar:\n\n'
                        for i, price in enumerate(products[:5], 1):
                            message += f'{i}. {price.text.strip()}\n'
                        await update.message.reply_text(message)
                    else:
                        await update.message.reply_text('❌ Ürün bulunamadı.')
                else:
                    await update.message.reply_text('❌ Arama sırasında bir hata oluştu.')

    except Exception as e:
        await update.message.reply_text(f'❌ Bir hata oluştu: {str(e)}')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        '🔍 Komut Listesi:\n\n'
        '/ara [ürün adı] - Ürün fiyatlarını arar\n'
        '/yardim - Bu menüyü gösterir\n\n'
        '📝 Örnek Kullanım:\n'
        '/ara ütü masası'
    )

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ara", search_product))
    application.add_handler(CommandHandler("yardim", help_command))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
