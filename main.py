import os
import time
import requests
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# ===== רשימת מניות למעקב =====
TICKERS = ["TSLA", "MSFT", "AAPL", "NVDA", "CELH"]

# ===== טען ENV =====
load_dotenv(dotenv_path=".env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")

# ===== פונקציות לטלגרם =====
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT, "text": text}
    requests.post(url, data=payload)

def send_telegram_image(path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": TELEGRAM_CHAT, "caption": caption}
        requests.post(url, files=files, data=data)

# ===== פונקציה ליצירת גרף וניתוח =====
def fetch_and_plot(ticker):
    data = yf.download(ticker, period="60d", interval="1h", auto_adjust=True)
    if data.empty:
        send_telegram(f"❌ אין נתונים זמינים עבור {ticker}")
        return

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    if 'Date' in data.columns:
        data.rename(columns={'Date': 'Datetime'}, inplace=True)

    data['Datetime'] = pd.to_datetime(data['Datetime'])
    data['MA150'] = data['Close'].rolling(window=150).mean()

    latest_price = round(data['Close'].iloc[-1], 2)
    latest_ma = round(data['MA150'].iloc[-1], 2)
    action = "📈 להחזיק / לחזק (המניה מעל ממוצע 150)" if latest_price > latest_ma else "📉 לשקול למכור (המניה מתחת לממוצע 150)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Datetime'], y=data['Close'], mode='lines', name='Close Price', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=data['Datetime'], y=data['MA150'], mode='lines', name='MA150', line=dict(color='red', width=2)))

    fig.update_layout(title=f'{ticker} Price Movement', xaxis_title='Datetime', yaxis_title='Price', template='plotly_dark', showlegend=True)
    graph_path = f"{ticker}_price.png"
    fig.write_image(graph_path)

    caption = f"""
📊 מניה: {ticker}
💰 מחיר נוכחי: {latest_price}$
📉 ממוצע 150: {latest_ma}$
📈 פעולה: {action}
"""
    send_telegram_image(graph_path, caption=caption.strip())

# ===== הרצה מחזורית =====
while True:
    for ticker in TICKERS:
        fetch_and_plot(ticker)
        time.sleep(5)  # מנוחה בין מניות כדי לא להעמיס

    # כל כמה זמן להפעיל שוב (שעה לדוגמה)
    print("מחכה שעה להרצה הבאה...")
    time.sleep(3600)
