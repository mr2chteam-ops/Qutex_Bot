import os
import time
import requests
import numpy as np

# Updated Telegram Bot Token
BOT_TOKEN = "8908381436:AAFYp7tXEZA7ygYYXYg45GhDj_djEwgy610"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ----------------- Real Technical Analysis Engine (Yahoo Finance) -----------------
def get_real_market_analysis(symbol, timeframe):
    try:
        # Convert Binance symbol format (e.g., BTCUSDT) to Yahoo Finance format (e.g., BTC-USD)
        yf_symbol = symbol.replace("USDT", "-USD")
        
        # Map timeframe to Yahoo Finance intervals
        tf_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
        interval = tf_map.get(timeframe, "1m")
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval={interval}&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return "⚠️ Failed to fetch data from market server. Please try again later."

        data = response.json()
        result = data.get('chart', {}).get('result')
        
        if not result:
            return "⚠️ Insufficient market data available."
            
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])
        
        # Clean None values if any
        closes = [c for c in closes if c is not None]
        
        if len(closes) < 30:
            return "⚠️ Insufficient market data available."

        closes = np.array(closes)

        def calculate_ema(prices, period):
            weights = np.exp(np.linspace(-1., 0., period))
            weights /= weights.sum()
            a = np.convolve(prices, weights, mode='valid')
            return a[-1]

        ema_9 = calculate_ema(closes, 9)
        ema_21 = calculate_ema(closes, 21)

        deltas = np.diff(closes)
        seed = deltas[:14]
        up = seed[seed >= 0].sum() / 14
        down = -seed[seed < 0].sum() / 14
        rs = up / down if down != 0 else 0
        rsi = 100.0 - (100.0 / (1.0 + rs))

        current_price = closes[-1]

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

        result_text = (
            f"📊 *LIVE MARKET ANALYSIS* 📊\n\n"
            f"🔹 *Market/Pair:* `{symbol}`\n"
            f"⏱ *Timeframe:* `{timeframe}`\n"
            f"💰 *Live Price:* `{current_price:.2f}`\n\n"
            f"📈 *Prediction:* {prediction}\n"
            f"🎯 *Confidence:* {confidence}\n"
            f"💡 *Analysis Reason:* {reason}"
        )
        return result_text

    except Exception as e:
        return f"Technical error occurred: {str(e)}"

# ----------------- Telegram Message Helper Functions -----------------
def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{BASE_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

# ----------------- Long Polling Loop -----------------
def main():
    print("Bot is running via Telegram HTTP API...")
    offset = 0
    user_selections = {}

    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]

                        if text == "/start":
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🪙 BTC/USDT", "callback_data": "BTCUSDT"},
                                     {"text": "🪙 ETH/USDT", "callback_data": "ETHUSDT"}],
                                    [{"text": "🪙 BNB/USDT", "callback_data": "BNBUSDT"},
                                     {"text": "🪙 SOL/USDT", "callback_data": "SOLUSDT"}]
                                ]
                            }
                            send_message(chat_id, "🤖 *Welcome to the Real-Time Trading Analysis Bot!*\n\nPlease select your preferred market:", reply_markup=keyboard)

                    elif "callback_query" in update:
                        query = update["callback_query"]
                        chat_id = query["message"]["chat"]["id"]
                        message_id = query["message"]["message_id"]
                        data_cb = query["data"]

                        if data_cb in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]:
                            user_selections[chat_id] = data_cb
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "⏱ 1 Minute (1m)", "callback_data": "tf_1m"},
                                     {"text": "⏱ 5 Minutes (5m)", "callback_data": "tf_5m"}],
                                    [{"text": "⏱ 15 Minutes (15m)", "callback_data": "tf_15m"}]
                                ]
                            }
                            edit_message(chat_id, message_id, f"Selected Pair: `{data_cb}`\n\nNow select your trading timeframe:", reply_markup=keyboard)

                        elif data_cb.startswith("tf_"):
                            timeframe = data_cb.split("_")[1]
                            symbol = user_selections.get(chat_id, "BTCUSDT")

                            edit_message(chat_id, message_id, f"🔄 Calculating live momentum and RSI for `{symbol}` on `{timeframe}` timeframe...")
                            
                            analysis_result = get_real_market_analysis(symbol, timeframe)
                            send_message(chat_id, analysis_result)

        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
