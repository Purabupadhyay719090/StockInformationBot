import os
import io
import matplotlib.pyplot as plt
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from yahooquery import search, Ticker
from datetime import datetime

# Replace this with environment variable if deploying securely
BOT_TOKEN = '7426180831:AAFE6Z6wqptydBGLe1bJczyG7KkvyVj3uUc'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /stock <Company Name> to get the stock price, prediction, and chart.")

async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /stock <Company Name>")
        return

    company_name = " ".join(context.args)

    try:
        results = search(company_name)
        quotes = results.get("quotes", [])

        if not quotes:
            await update.message.reply_text(f"No results found for '{company_name}'.")
            return

        best_match = quotes[0]
        ticker = best_match.get("symbol")
        name = best_match.get("shortname", ticker)

        stock = Ticker(ticker)
        price_data = stock.price.get(ticker)

        if not isinstance(price_data, dict):
            await update.message.reply_text(f"Could not retrieve stock data for `{ticker}`.")
            return

        price = price_data.get("regularMarketPrice")
        change_percent = price_data.get("regularMarketChangePercent")

        if price is None or change_percent is None:
            await update.message.reply_text(f"Could not retrieve full stock data for `{ticker}`.")
            return

        predicted_price = price * (1 + (change_percent / 100))

        response = (
            f"*{name}* (`{ticker}`)\n"
            f"💵 Price: ${float(price):.2f}\n"
            f"📉 Change: {float(change_percent):.2f}%\n\n"
            f"📈 *Predicted Next Price*: ~${float(predicted_price):.2f}"
        )
        await update.message.reply_text(response, parse_mode='Markdown')

        history = stock.history(period='1mo', interval='1d')
        if history.empty:
            await update.message.reply_text("No chart data available.")
            return

        history = history.reset_index()
        dates = [datetime.strftime(d, '%b %d') for d in history['date']]
        closes = history['close']

        plt.figure(figsize=(10, 4))
        plt.plot(dates, closes, marker='o', linestyle='-')
        plt.title(f"{ticker} - Last 30 Days")
        plt.xlabel("Date")
        plt.ylabel("Closing Price ($)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        await update.message.reply_photo(photo=InputFile(buf, filename=f"{ticker}_chart.png"))

    except Exception as e:
        await update.message.reply_text(f"Error fetching stock data: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stock", get_stock))

    PORT = int(os.environ.get("PORT", 8443))  # Render sets PORT automatically
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://<your-service-name>.onrender.com/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
