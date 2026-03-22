import os
import logging
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 1. Define the Handler Class
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
    
    # Silence the logs so they don't clutter Telegram bot logs
    def log_message(self, format, *args):
        return

# 2. Define the Server Starter
def run_health_check():
    # Render assigns a dynamic port via the PORT env var
    port = int(os.environ.get("PORT", 7860)) 
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server started on port {port}")
    server.serve_forever()

# 3. START THE THREAD BEFORE ANYTHING ELSE
# This allows the health check to run while the bot initializes
threading.Thread(target=run_health_check, daemon=True).start()

import engine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in .env file!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user.first_name
    welcome_msg = (
        f"Hello {user}! \n\n"
        f"I am your Corporate Assistant Bot. I can answer questions based on our internal documents.\n\n"
        f"Try asking me a question using the /ask command.\n"
        f"Example: `/ask What is the hybrid work policy?`"
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a list of available commands."""
    help_msg = (
        "*Available Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/ask <your question> - Ask a question to the knowledge base"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the RAG queries."""
    user_query = " ".join(context.args)
    
    # Check if the user actually typed a question
    if not user_query:
        await update.message.reply_text(
            "Please provide a question.\nUsage: `/ask <your question>`", 
            parse_mode='Markdown'
        )
        return

    # 1. UX: Send an immediate "thinking" message
    status_message = await update.message.reply_text("*Searching knowledge base...*", parse_mode='Markdown')

    try:
        # 2. Run the heavy RAG task in a separate thread so the bot doesn't freeze
        answer, sources = await asyncio.to_thread(engine.generate_answer, user_query)
        
        # 3. Format the final reply
        if sources:
            source_list = ", ".join(sources)
            reply = f"{answer}\n\n*Sources:* {source_list}"
        else:
            reply = f"{answer}"

        # 4. Edit the original "thinking" message with the real answer
        await status_message.edit_text(reply, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error during RAG generation: {e}")
        await status_message.edit_text("Sorry, I encountered an internal error. Please try again later.")


if __name__ == '__main__':
    logger.info("Starting bot...")
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask))
    
    logger.info("Bot is running and polling for messages!")

    app.run_polling()