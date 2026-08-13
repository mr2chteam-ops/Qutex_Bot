import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
import requests
import numpy as np

# Logging Setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Put your Telegram Bot Token here
BOT_TOKEN = "8908381436:AAFYp7tXEZA7ygYYXYg45GhDj_djEwgy610"

# ----------------- Real Technical Analysis Engine (Without Pandas) -----------------
def get_real_market_analysis(symbol, timeframe):
    try:
        # Fetch real-time candlestick data from Binance Public API (Last 100 candles)
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=100"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return "⚠️ Failed to fetch data from market server. Please try again later."

        data = response.json()
        if not isinstance(data, list) or len(data) < 50:
            return "⚠️ Insufficient market data available."

        # Extract closing prices into a list/numpy array (Index 4 is the close price in Binance klines)
        closes = np.array([float(candle[4]) for candle in data])

        # 1. Calculate Exponential Moving Average (EMA 9 and EMA 21) using NumPy
        def calculate_ema(prices, period):
            weights = np.exp(np.linspace(-1., 0., period))
            weights /= weights.sum()
            a = np.convolve(prices, weights, mode='valid')
            return a[-1]

        ema_9 = calculate_ema(closes, 9)
        ema_21 = calculate_ema(closes, 21)

        # 2. Calculate RSI (Relative Strength Index - 14 Period)
        deltas = np.diff(closes)
        seed = deltas[:14]
        up = seed[seed >= 0].sum() / 14
        down = -seed[seed < 0].sum() / 14
        rs = up / down if down != 0 else 0
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # Get current real values
        current_price = closes[-1]

        # Trading Decision Logic (Real Strategy)
        if ema_9 > ema_21 and rsi > 50 and rsi < 70:
            prediction = "🟢 **UP (CALL) - Strong Bullish Trend**"
            confidence = "High"
            reason = f"EMA 9 is above EMA 21 and RSI ({rsi:.2f}) is in the bullish zone."
        elif ema_9 < ema_21 and rsi < 50 and rsi > 30:
            prediction = "🔴 **DOWN (PUT) - Strong Bearish Trend**"
            confidence = "High"
            reason = f"EMA 9 is below EMA 21 and RSI ({rsi:.2f}) is in the bearish zone."
        elif rsi >= 70:
            prediction = "⚠️ **OVERBOUGHT (Caution)**"
            confidence = "Low (Correction expected anytime)"
            reason = f"RSI is extremely high ({rsi:.2f}), market is overbought."
        elif rsi <= 30:
            prediction = "⚠️ **OVERSOLD (Caution)**"
            confidence = "Low (Bounce expected anytime)"
            reason = f"RSI is extremely low ({rsi:.2f}), market is oversold."
        else:
            prediction = "🟡 **SIDEWAYS / NEUTRAL (Hold)**"
            confidence = "Medium"
            reason = f"Market is currently showing no clear direction (RSI: {rsi:.2f})."

        # Format final result message
        result_text = (
            f"📊 **LIVE MARKET ANALYSIS** 📊\n\n"
            f"🔹 **Market/Pair:** `{symbol}`\n"
            f"⏱ **Timeframe:** `{timeframe}`\n"
            f"💰 **Live Price:** `{current_price}`\n\n"
            f"📈 **Prediction:** {prediction}\n"
            f"🎯 **Confidence:** {confidence}\n"
            f"💡 **Analysis Reason:** {reason}\n\n"
            f"⚡ *Note: Analysis is based on real-time mathematical indicator data.*"
        )
        return result_text

    except Exception as e:
        return f"Technical error occurred: {str(e)}"

# ----------------- Telegram Handlers -----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🪙 BTC/USDT", callback_data="BTCUSDT"),
         InlineKeyboardButton("🪙 ETH/USDT", callback_data="ETHUSDT")],
        [InlineKeyboardButton("🪙 BNB/USDT", callback_data="BNBUSDT"),
         InlineKeyboardButton("🪙 SOL/USDT", callback_data="SOLUSDT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 **Welcome to the Real-Time Trading Analysis Bot!**\n\nPlease select your preferred market from the list below:", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # If user selects a coin
    if data in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]:
        context.user_data['symbol'] = data
        
        # Give option to select timeframe
        keyboard = [
            [InlineKeyboardButton("⏱ 1 Minute (1m)", callback_data="tf_1m"),
             InlineKeyboardButton("⏱ 5 Minutes (5m)", callback_data="tf_5m")],
            [InlineKeyboardButton("⏱ 15 Minutes (15m)", callback_data="tf_15m")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Selected Pair: `{data}`\n\nNow select your trading timeframe:", 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    # If user selects a timeframe
    elif data.startswith("tf_"):
        timeframe = data.split("_")[1]
        symbol = context.user_data.get('symbol', 'BTCUSDT')

        await query.edit_message_text(text=f"🔄 Calculating live momentum and RSI for `{symbol}` on `{timeframe}` timeframe...", parse_mode="Markdown")

        # Process real data and get analysis
        analysis_result = get_real_market_analysis(symbol, timeframe)

        # Send final signal to user
        await query.message.reply_text(analysis_result, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Real-time trading bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
