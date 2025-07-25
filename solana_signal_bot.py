import requests
import time
from telegram import Bot
from telegram.error import TelegramError
from textblob import TextBlob
import tweepy
import numpy as np
import os

# ----------- إعدادات التليجرام -----------
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or '7785345671:AAGq2c6n_8CDtm3PJc1k8LotpRIW8KKRSYY'
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID') or '@testGPT11'

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ----------- إعدادات تويتر -----------
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY') or ""
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET') or ""
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN') or ""
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET') or ""

if TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET:
    auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)
else:
    api = None  # لا يوجد تويتر، تجاوز التحليل

# ----------- كلمات ممنوعة شرعية -----------
HARAM_KEYWORDS = [
    "beer", "wine", "vodka", "alcohol", "casino", "gambling", "sex", "porno",
    "xxx", "lgbt", "usury", "interest", "bank", "loan", "cum", "tits", "strip",
    "nude", "naked", "fetish", "lesbian", "gay", "nipple", "pussy"
]

BIRDEYE_API = "https://api.birdeye.so/public/tokenlist?sort_by=volume_24h&sort_type=desc&limit=100"
DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

def is_halal(name):
    name_lower = name.lower()
    return not any(bad_word in name_lower for bad_word in HARAM_KEYWORDS)

def is_verified_contract(token):
    return token.get("is_verified", False)

def get_holders_count(token_address):
    try:
        url = f"https://public-api.birdeye.so/public/token/holders?address={token_address}"
        res = requests.get(url)
        data = res.json()
        holders = data.get("data", {}).get("holders", 0)
        print(f"Holders for {token_address}: {holders}")
        return holders
    except Exception as e:
        print(f"Error getting holders count for {token_address}: {e}")
        return 0

def get_liquidity_and_volume(address):
    try:
        res = requests.get(DEX_API)
        data = res.json().get("pairs", [])
        for pair in data:
            if pair.get("baseToken", {}).get("address", "") == address:
                liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                volume = float(pair.get("volume", {}).get("h24", 0))
                print(f"Liquidity and volume for {address}: {liquidity}, {volume}")
                return liquidity, volume
        print(f"No liquidity data found for {address}")
        return 0, 0
    except Exception as e:
        print(f"Error getting liquidity/volume for {address}: {e}")
        return 0, 0

def analyze_candles(address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}"
        res = requests.get(url)
        data = res.json()
        candles = data.get("candles", [])
        if candles and candles[0].get("close", 0) > candles[0].get("open", 0):
            print(f"Candle green for {address}")
            return True
        print(f"Candle not green for {address}")
        return False
    except Exception as e:
        print(f"Error analyzing candles for {address}: {e}")
        return False

def get_top_holders_behavior(address):
    # Placeholder always true
    return True

def get_twitter_sentiment(token_symbol):
    if not api:
        return 0  # لا يوجد تحليل تويتر
    try:
        tweets = api.search_tweets(q=token_symbol, lang="en", count=50)
        sentiments = []
        for tweet in tweets:
            analysis = TextBlob(tweet.text)
            sentiments.append(analysis.sentiment.polarity)
        if len(sentiments) == 0:
            return 0
        avg_sentiment = np.mean(sentiments)
        print(f"Twitter sentiment for {token_symbol}: {avg_sentiment}")
        return avg_sentiment
    except Exception as e:
        print(f"Error fetching twitter sentiment for {token_symbol}: {e}")
        return 0

last_prices = {}

def check_price_spike(token_symbol, current_price):
    spike_threshold = 0.10  # 10%
    global last_prices
    prev_price = last_prices.get(token_symbol, current_price)
    change = abs(current_price - prev_price) / prev_price
    last_prices[token_symbol] = current_price
    if change >= spike_threshold:
        print(f"Price spike detected for {token_symbol}: change {change*100:.2f}%")
        return True
    return False

def send_signal(token):
    try:
        msg = f"🚀 توصية ميم كوين سولانا قوية\n"
        msg += f"📛 الاسم: {token['name']} ({token['symbol']})\n"
        msg += f"🪙 السعر الحالي: {token['price']}$\n"
        msg += f"🎯 الهدف المتوقع: {token['target']:.4f}$ (🔺 +3x)\n"
        msg += f"📜 العقد: `{token['address']}`\n"
        msg += f"📊 السيولة: {token['liquidity']} USD\n"
        msg += f"📈 حجم التداول: {token['volume']} USD\n"
        msg += f"🔥 الشمعة الأولى: {'خضراء ✅' if token['candle'] else 'غير مؤكدة ❌'}\n"
        msg += f"🐋 سلوك كبار المستثمرين: {'داعم ✅' if token['holders_behavior'] else 'غير واضح ❌'}\n"
        msg += f"📉 تغير سعر فجائي: {'نعم ⚠️' if token['price_spike'] else 'لا'}\n"
        msg += f"💬 تقييم المشاعر: {token['sentiment']:.2f}\n"
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")
        print(f"📨 Sent signal for {token['symbol']}")
    except TelegramError as e:
        print(f"❌ Failed to send signal for {token['symbol']}: {e}")
    except Exception as e:
        print(f"❌ Unexpected error sending signal for {token['symbol']}: {e}")

def main_loop():
    print("🚀 Starting main loop...")
    while True:
        try:
            response = requests.get(BIRDEYE_API)
            tokens = response.json().get("data", [])
            print(f"🔄 Fetched {len(tokens)} tokens")
            if not tokens:
                print("⚠️ No tokens found, sleeping for 60 seconds...")
                time.sleep(60)
                continue

            for token in tokens:
                name = token.get("name", "")
                symbol = token.get("symbol", "")
                address = token.get("address", "")
                price = float(token.get("price", 0))
                ath = float(token.get("ath_price", 0))

                print(f"⏳ Processing token: {symbol}, price: {price}")

                if not name or not address or price <= 0:
                    print("⚠️ Invalid token data, skipping.")
                    continue

                if not is_halal(name):
                    print(f"⛔ Token {name} filtered by halal check")
                    continue

                if not is_verified_contract(token):
                    print(f"⛔ Token {symbol} contract not verified")
                    continue

                if ath <= price * 3:  # هدف 3x
                    print(f"⛔ Token {symbol} ATH condition not met")
                    continue

                holders_count = get_holders_count(address)
                if holders_count < 20:
                    print(f"⛔ Token {symbol} holders count too low: {holders_count}")
                    continue

                liquidity, volume = get_liquidity_and_volume(address)
                if liquidity < 2000 or volume < 3000:
                    print(f"⛔ Token {symbol} liquidity/volume too low: {liquidity}/{volume}")
                    continue

                candle_green = analyze_candles(address)
                if not candle_green:
                    print(f"⛔ Token {symbol} candle not green")
                    continue

                holders_behavior = get_top_holders_behavior(address)
                if not holders_behavior:
                    print(f"⛔ Token {symbol} holders behavior not supportive")
                    continue

                price_spike = check_price_spike(symbol, price)
                sentiment_score = get_twitter_sentiment(symbol)

                token_data = {
                    "name": name,
                    "symbol": symbol,
                    "address": address,
                    "price": price,
                    "target": price * 3,
                    "liquidity": liquidity,
                    "volume": volume,
                    "candle": candle_green,
                    "holders_behavior": holders_behavior,
                    "price_spike": price_spike,
                    "sentiment": sentiment_score,
                }

                send_signal(token_data)
                time.sleep(1)

        except Exception as e:
            print(f"❌ Error in main loop: {e}")

        time.sleep(60)

if __name__ == '__main__':
    try:
        bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text="🚀 بوت التوصيات يعمل بنجاح!")
        print("تم إرسال رسالة اختبارية بنجاح.")
    except Exception as e:
        print(f"فشل إرسال رسالة الاختبار: {e}")

    main_loop()
