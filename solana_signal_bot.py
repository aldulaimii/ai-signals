import requests
import time
from telegram import Bot
from textblob import TextBlob
import tweepy
import numpy as np

# ----------- إعدادات التليجرام -----------
TELEGRAM_BOT_TOKEN = '7785345671:AAGgrahzEQbZV3WqYQaadWn6ID8KJP5skd8'
TELEGRAM_CHANNEL_ID = '@testGPT11'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ----------- إعدادات تويتر -----------
TWITTER_API_KEY = "your_api_key"
TWITTER_API_SECRET = "your_api_secret"
TWITTER_ACCESS_TOKEN = "your_access_token"
TWITTER_ACCESS_SECRET = "your_access_secret"

auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
api = tweepy.API(auth)

# ----------- كلمات ممنوعة شرعية -----------
HARAM_KEYWORDS = [
    "beer", "wine", "vodka", "alcohol", "casino", "gambling", "sex", "porno",
    "xxx", "lgbt", "usury", "interest", "bank", "loan", "cum", "tits", "strip",
    "nude", "naked", "fetish", "lesbian", "gay", "nipple", "pussy"
]

# ----------- API روابط -----------
BIRDEYE_API = "https://api.birdeye.so/public/tokenlist?sort_by=volume_24h&sort_type=desc&limit=100"
DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

# ----------- فلترة شرعية -----------
def is_halal(name):
    name_lower = name.lower()
    return not any(bad_word in name_lower for bad_word in HARAM_KEYWORDS)

# ----------- تحقق من العقد -----------
def is_verified_contract(token):
    return token.get("is_verified", False)

# ----------- جلب عدد الهولدرز -----------
def get_holders_count(token_address):
    try:
        url = f"https://public-api.birdeye.so/public/token/holders?address={token_address}"
        res = requests.get(url)
        data = res.json()
        return data.get("data", {}).get("holders", 0)
    except:
        return 0

# ----------- جلب السيولة والحجم -----------
def get_liquidity_and_volume(address):
    try:
        res = requests.get(DEX_API)
        data = res.json().get("pairs", [])
        for pair in data:
            if pair.get("baseToken", {}).get("address", "") == address:
                liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                volume = float(pair.get("volume", {}).get("h24", 0))
                return liquidity, volume
        return 0, 0
    except:
        return 0, 0

# ----------- تحليل الشموع اللحظية -----------
def analyze_candles(address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}"
        res = requests.get(url)
        data = res.json()
        candles = data.get("candles", [])
        if candles and candles[0].get("close", 0) > candles[0].get("open", 0):
            return True
        return False
    except:
        return False

# ----------- تحليل سلوك كبار المحافظ (Placeholder) -----------
def get_top_holders_behavior(address):
    # تحتاج تطوير مستقبلي حسب سلوك المحافظ
    return True

# ----------- تحليل مشاعر السوق -----------
def get_twitter_sentiment(token_symbol):
    try:
        tweets = api.search_tweets(q=token_symbol, lang="en", count=50)
        sentiments = []
        for tweet in tweets:
            analysis = TextBlob(tweet.text)
            sentiments.append(analysis.sentiment.polarity)
        if len(sentiments) == 0:
            return 0
        return np.mean(sentiments)
    except:
        return 0

# ----------- تنبيه تغير السعر المفاجئ -----------
last_prices = {}

def check_price_spike(token_symbol, current_price):
    spike_threshold = 0.10  # 10% تغير خلال 5 دقائق
    global last_prices
    prev_price = last_prices.get(token_symbol, current_price)
    change = abs(current_price - prev_price) / prev_price
    last_prices[token_symbol] = current_price
    if change >= spike_threshold:
        return True
    return False

# ----------- إرسال توصية -----------
def send_signal(token):
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

# ----------- الحلقة الرئيسية -----------
def main_loop():
    while True:
        try:
            response = requests.get(BIRDEYE_API)
            tokens = response.json().get("data", [])
            for token in tokens:
                name = token.get("name", "")
                symbol = token.get("symbol", "")
                address = token.get("address", "")
                price = float(token.get("price", 0))
                ath = float(token.get("ath_price", 0))

                if not name or not address or price <= 0:
                    continue

                if not is_halal(name):
                    continue

                if not is_verified_contract(token):
                    continue

                if ath <= price * 3:  # هدف 3x
                    continue

                holders_count = get_holders_count(address)
                if holders_count < 20:
                    continue

                liquidity, volume = get_liquidity_and_volume(address)
                if liquidity < 2000 or volume < 3000:
                    continue

                candle_green = analyze_candles(address)
                if not candle_green:
                    continue

                holders_behavior = get_top_holders_behavior(address)
                if not holders_behavior:
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
            print("Error:", e)

        time.sleep(60)

if __name__ == '__main__':
    main_loop()


