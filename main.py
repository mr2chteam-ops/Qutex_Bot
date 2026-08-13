import logging
import os
from flask import Flask, request
import requests
import telebot
from telebot import types

# New Bot Token
TOKEN = "8908381436:AAGeva6PKOPFPPUcx36tKUuUA4rQne5CmlM"
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# IMPORTANT: Update this URL with your actual Render service URL
RENDER_URL = "https://qutex-bot.onrender.com"

@app.route("/")
def home():
    return "Trading Bot is active."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Forbidden", 403

def analyze_market(symbol, timeframe):
    interval_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
    tf = interval_map.get(timeframe, "1m")
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not isinstance(data, list) or len(data) < 20:
            return None, None, None, "Market data unavailable"
        
        closes = [float(entry[4]) for entry in data]
        live_price = closes[-1]
        
        gains, losses = 0, 0
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff > 0: gains += diff
            else: losses -= diff
            
        avg_gain = gains / 14
        avg_loss = losses / 14 if losses != 0 else 1
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        ema_short = sum(closes[-5:]) / 5
        ema_long = sum(closes[-15:]) / 15
        
        if rsi < 45 or (ema_short > ema_long and rsi < 70):
            prediction = "UP (CALL) - Buy Signal"
            confidence = "High" if rsi < 35 or rsi > 65 else "Moderate"
            reason = f"Bullish EMA trend and RSI is {rsi:.2f}."
        else:
            prediction = "DOWN (PUT) - Sell Signal"
            confidence = "High" if rsi > 70 or rsi < 30 else "Moderate"
            reason = f"Bearish EMA trend and RSI is {rsi:.2f}."
            
        return live_price, prediction, confidence, reason
    except Exception as e:
        return None, None, None, str(e)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("BTC/USDT (1m)", callback_data="BTCUSDT_1m"),
        types.InlineKeyboardButton("BTC/USDT (5m)", callback_data="BTCUSDT_5m"),
        types.InlineKeyboardButton("ETH/USDT (1m)", callback_data="ETHUSDT_1m"),
        types.InlineKeyboardButton("SOL/USDT (1m)", callback_data="SOLUSDT_1m")
    )
    bot.send_message(message.chat.id, "Select a market for analysis:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if "_" in call.data:
        symbol, timeframe = call.data.split("_")
        bot.answer_callback_query(call.id, "Analyzing...")
        
        live_price, prediction, confidence, reason = analyze_market(symbol, timeframe)
        
        if live_price is None:
            bot.send_message(call.message.chat.id, "Error fetching data.")
            return

        text = (f"ANALYSIS REPORT\n\n"
                f"Pair: {symbol}\n"
                f"Price: {live_price}\n"
                f"Prediction: {prediction}\n"
                f"Confidence: {confidence}\n"
                f"Reason: {reason}")
        bot.send_message(call.message.chat.id, text)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
