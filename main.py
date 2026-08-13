import logging
import os
import threading
from flask import Flask
import requests
import telebot
from telebot import types

# Bot Token provided by user
TOKEN = "8908381436:AAGeva6PKOPFPPUcx36tKUuUA4rQne5CmlM"
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)

# 1. Flask server to satisfy Render port binding requirements
app = Flask(__name__)


@app.route("/")
def home():
  return "Trading Bot is running live and healthy!"


def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Real-time market data analysis function using Binance API
def analyze_market(symbol, timeframe):
  interval_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
  tf = interval_map.get(timeframe, "1m")

  url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"

  try:
    response = requests.get(url, timeout=10)
    data = response.json()

    if not isinstance(data, list) or len(data) < 20:
      return None, None, None, "Not enough market data available"

    # Extract closing prices
    closes = [float(entry[4]) for entry in data]
    live_price = closes[-1]

    # Technical Indicator Calculation (RSI)
    gains, losses = 0, 0
    for i in range(1, len(closes)):
      diff = closes[i] - closes[i - 1]
      if diff > 0:
        gains += diff
      else:
        losses -= diff

    avg_gain = gains / 14
    avg_loss = losses / 14 if losses != 0 else 1
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Technical Indicator Calculation (EMA)
    ema_short = sum(closes[-5:]) / 5
    ema_long = sum(closes[-15:]) / 15

    # Signal Generation logic based on technical analysis
    if rsi < 45 or (ema_short > ema_long and rsi < 70):
      prediction = "🟢 UP (CALL) - Buy Signal"
      confidence = "High" if rsi < 35 or rsi > 65 else "Moderate"
      reason = (
          f"EMA trend is bullish and RSI is at {rsi:.2f}, indicating strong"
          " upward momentum."
      )
    else:
      prediction = "🔴 DOWN (PUT) - Sell Signal"
      confidence = "High" if rsi > 70 or rsi < 30 else "Moderate"
      reason = (
          f"EMA trend is bearish and RSI is at {rsi:.2f}, indicating downward"
          " pressure."
      )

    return live_price, prediction, confidence, reason

  except Exception as e:
    print(f"Error fetching data: {e}")
    return None, None, None, str(e)


# 3. Start command and Interactive Inline Keyboard setup
@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "🪙 BTC/USDT (1m)", callback_data="BTCUSDT_1m"
      ),
      types.InlineKeyboardButton(
          "🪙 BTC/USDT (5m)", callback_data="BTCUSDT_5m"
      ),
      types.InlineKeyboardButton(
          "🪙 ETH/USDT (1m)", callback_data="ETHUSDT_1m"
      ),
      types.InlineKeyboardButton(
          "🪙 SOL/USDT (1m)", callback_data="SOLUSDT_1m"
      ),
  )

  welcome_text = (
      "🤖 *Professional Trading Signal Bot*\n\nPlease select a market and"
      " timeframe to get real-time analysis:"
  )
  bot.send_message(
      message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup
  )


# 4. Callback query handler for button clicks and real-time report delivery
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
  if "_" in call.data:
    parts = call.data.split("_")
    symbol = parts[0]
    timeframe = parts[1]

    bot.answer_callback_query(
        call.id,
        f"Analyzing live market for {symbol} ({timeframe})... Please wait.",
    )

    live_price, prediction, confidence, reason = analyze_market(
        symbol, timeframe
    )

    if live_price is None:
      bot.send_message(
          call.message.chat.id,
          "⚠️ Failed to fetch market data from API. Please try again later.",
      )
      return

    analysis_text = (
        f"📊 *REAL-TIME SIGNAL ANALYSIS* 📊\n\n"
        f"🔹 *Market/Pair:* {symbol}\n"
        f"⏱ *Timeframe:* {timeframe}\n"
        f"💰 *Live Price:* {live_price}\n\n"
        f"📈 *Prediction:* {prediction}\n"
        f"🎯 *Confidence:* {confidence}\n"
        f"💡 *Reason:* {reason}"
    )

    bot.send_message(
        call.message.chat.id, analysis_text, parse_mode="Markdown"
    )


# 5. Main execution block combining Flask server and Telegram bot polling
if __name__ == "__main__":
  server_thread = threading.Thread(target=run_web_server)
  server_thread.daemon = True
  server_thread.start()

  print("Professional Trading Bot is running with polling...")
  bot.infinity_polling(none_stop=True, interval=0, timeout=20)
