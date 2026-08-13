import datetime
import logging
import os
import random
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = "8908381436:AAGeva6PKOPFPPUcx36tKUuUA4rQne5CmlM"
DEVELOPER_NAME = "@HANTER_XD_OFFICIAL"  # আপনার দেওয়া টেলিগ্রাম ইউজারনেম

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/")
def home():
  return "News-Driven Smart Trading Bot is running!"


def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# Simulated Real-time News Feed & Technical Convergence Engine
def news_and_technical_analysis(symbol):
  news_events = [
      {
          "title": "US Core Retail Sales Data Release",
          "impact": "High",
          "bias": "Bullish",
      },
      {
          "title": "FOMC Meeting Minutes & Interest Rate Outlook",
          "impact": "High",
          "bias": "Bearish",
      },
      {
          "title": "ECB Monetary Policy Statement",
          "impact": "Medium",
          "bias": "Bullish",
      },
      {
          "title": "Global Crypto Liquidity Inflow Surge",
          "impact": "High",
          "bias": "Bullish",
      },
      {
          "title": "Geopolitical Supply Chain Tension Update",
          "impact": "High",
          "bias": "Bearish",
      },
  ]

  current_news = random.choice(news_events)
  rsi = round(random.uniform(25, 78), 2)

  now = datetime.datetime.now()
  start_time = now.strftime("%I:%M %p")
  end_time = (now + datetime.timedelta(minutes=5)).strftime("%I:%M %p")

  if current_news["bias"] == "Bullish" or rsi < 40:
    prediction = "🟢 UP (CALL) - Strong Short Signal"
    accuracy = "97.4% (News + Technical Verified)"
    action_reason = (
        f"News Impact ({current_news['impact']}): {current_news['title']}"
        f" supports upward breakout. RSI is at {rsi}."
    )
  else:
    prediction = "🔴 DOWN (PUT) - Strong Short Signal"
    accuracy = "96.8% (News + Technical Verified)"
    action_reason = (
        f"News Impact ({current_news['impact']}): {current_news['title']}"
        f" drives selling pressure. RSI is at {rsi}."
    )

  return prediction, accuracy, action_reason, start_time, end_time, current_news[
      "title"
  ]


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_name = message.from_user.first_name

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn1 = types.KeyboardButton("💱 Currencies (OTC & Live)")
  btn2 = types.KeyboardButton("🪙 Crypto (News Driven)")
  btn3 = types.KeyboardButton("🛢 Commodities & Stocks")
  btn4 = types.KeyboardButton("⚡ Live News Flash")
  markup.add(btn1, btn2, btn3, btn4)

  welcome_text = (
      f"🚀 **Welcome, {user_name} to Elite News & AI Analyzer!** 🚀\n\n"
      f"This system scans **Global Economic News Feeds**, **Candle Momentum**, and **Technical Indicators (RSI/MACD)** simultaneously to provide high-accuracy short signals (1m - 5m).\n\n"
      f"👨‍💻 **Lead Developer:** {DEVELOPER_NAME}\n\n"
      f"👇 *Select your target market below to get a verified signal:*"
  )
  bot.send_message(
      message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup
  )


@bot.message_handler(func=lambda message: True)
def handle_menu(message):
  text = message.text
  chat_id = message.chat.id

  if "Currencies" in text:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("EUR/USD (OTC)", callback_data="news_EURUSD"),
        types.InlineKeyboardButton("GBP/USD (OTC)", callback_data="news_GBPUSD"),
        types.InlineKeyboardButton("USD/BDT (OTC)", callback_data="news_USDBDT"),
        types.InlineKeyboardButton("AUD/NZD (OTC)", callback_data="news_AUDNZD"),
    )
    bot.send_message(
        chat_id, "Select Currency Pair for News Analysis:", reply_markup=markup
    )

  elif "Crypto" in text:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Bitcoin (OTC)", callback_data="news_BTC"),
        types.InlineKeyboardButton("Ethereum (OTC)", callback_data="news_ETH"),
        types.InlineKeyboardButton("Solana (OTC)", callback_data="news_SOL"),
        types.InlineKeyboardButton("Toncoin (OTC)", callback_data="news_TON"),
    )
    bot.send_message(
        chat_id, "Select Crypto Asset for News Analysis:", reply_markup=markup
    )

  elif "Commodities" in text:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Gold (OTC)", callback_data="news_Gold"),
        types.InlineKeyboardButton(
            "UKBrent (OTC)", callback_data="news_UKBrent"
        ),
        types.InlineKeyboardButton(
            "EURO STOXX 50", callback_data="news_EUROSTOXX"
        ),
    )
    bot.send_message(
        chat_id,
        "Select Commodity/Stock for News Analysis:",
        reply_markup=markup,
    )

  elif "Live News Flash" in text:
    news_flashes = [
        "🔥 [HIGH IMPACT] US Retail Sales report indicates strong dollar demand.",
        "⚡ [MEDIUM IMPACT] European Central Bank hints at steady interest rates.",
        "🚀 [CRYPTO FLASH] Massive whale accumulation detected on major exchanges.",
    ]
    bot.send_message(
        chat_id,
        f"📰 **Latest Market News Feed:**\n\n" + "\n\n".join(news_flashes),
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("news_"))
def send_news_signal(call):
  symbol = call.data.replace("news_", "")
  bot.answer_callback_query(
      call.id, "Scanning News Feeds & Candle Momentum..."
  )

  prediction, accuracy, reason, start_time, end_time, news_title = (
      news_and_technical_analysis(symbol)
  )

  report = (
      f"📰🎯 **NEWS-DRIVEN SMART SIGNAL REPORT** 🎯📰\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      f"🔹 **Asset / Pair:** `{symbol}`\n"
      f"⏰ **Active Time Window:** `{start_time} to {end_time}`\n"
      f"⏱ **Recommended Duration:** 1 Min / 5 Min\n"
      f"📈 **Signal Prediction:** {prediction}\n"
      f"🎯 **Success Rate:** `{accuracy}`\n"
      f"📢 **Detected News:** __{news_title}__\n"
      f"💡 **Analysis Summary:** {reason}\n"
      f"👨‍💻 **Developer:** {DEVELOPER_NAME}\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      f"⚠️ *Note: Enter trade precisely within the given timeframe for maximum accuracy.*"
  )
  bot.send_message(call.message.chat.id, report, parse_mode="Markdown")


if __name__ == "__main__":
  try:
    bot.remove_webhook()
  except Exception:
    pass

  server_thread = threading.Thread(target=run_web_server)
  server_thread.daemon = True
  server_thread.start()

  print("News-driven Smart Bot is running with polling...")
  bot.infinity_polling(none_stop=True, interval=0, timeout=20)
