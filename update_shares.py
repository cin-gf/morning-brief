import os
import re
import yfinance as ticker_api
from bs4 import BeautifulSoup

# 1. 設定你的 HTML 檔案名稱
html_filename = "2026-05-22-早晨_3.html"

if not os.path.exists(html_filename):
    print(f"找不到檔案: {html_filename}")
    exit()

# 讀取 HTML
with open(html_filename, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# 2. 定義要更新的台股代號 (Yahoo 格式需要加 .TW)
# 這裡對應你 HTML 裡的股票代號
stock_mapping = {
    "0050": "0050.TW",
    "0056": "0056.TW",
    "00878": "00878.TW",
    "00919": "00919.TW",
    "006208": "006208.TW",
    "2330": "2330.TW",
    "2303": "2303.TW",
    "2409": "2409.TW",
    "3189": "3189.TW",
    "2313": "2313.TW",
    "2353": "2353.TW",
    "2324": "2324.TW",
    "8046": "8046.TW",
    "2454": "2454.TW",
    "3711": "3711.TW",
    "1785": "1785.TW",
}

print("開始從 Yahoo Finance 抓取最新數據...")

# 尋找網頁中所有的股票卡片
stock_cards = soup.find_all("div", class_="stock-card")

for card in stock_cards:
    code_el = card.find("div", class_="stock-card-code")
    if not code_el:
        continue
    
    code = code_el.text.strip()
    
    # 如果這檔股票在我們的更新清單中
    if code in stock_mapping:
        yahoo_code = stock_mapping[code]
        try:
            # 抓取 Yahoo 資料
            ticker = ticker_api.Ticker(yahoo_code)
            todays_data = ticker.history(period="1d")
            
            if todays_data.empty:
                continue
                
            # 取得最新收盤價、前一日收盤價、成交量
            current_price = todays_data['Close'].iloc[-1]
            prev_close = ticker.info.get('previousClose', current_price)
            volume_shares = todays_data['Volume'].iloc[-1] # 這是「股數」
            volume_cards = int(volume_shares / 1000) # 轉換成台股習慣的「張數」
            
            # 計算漲跌幅
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # --- 開始更新 HTML DOM ---
            # 1. 更新價格
            price_el = card.find("span", class_="stock-card-price")
            if price_el:
                price_el.string = f"${current_price:,.2f}" if current_price % 1 != 0 else f"${int(current_price):,}"

            # 2. 更新漲跌幅標籤與顏色
            change_el = card.find("span", class_="stock-card-change")
            if change_el:
                if change_pct > 0:
                    change_el.string = f"▲ +{change_pct:.2f}%"
                    change_el['class'] = ['stock-card-change', 'up']
                elif change_pct < 0:
                    change_el.string = f"▼ {change_pct:.2f}%"
                    change_el['class'] = ['stock-card-change', 'down']
                else:
                    change_el.string = f"  0.00%"
                    change_el['class'] = ['stock-card-change', 'flat']
            
            # 3. 更新成交量
            vol_val_el = card.find("span", class_="vol-value")
            if vol_val_el:
                vol_val_el.string = f"{volume_cards:,} 張"
                
            print(f"成功更新 {code}: {current_price} | {change_pct:.2f}% | {volume_cards}張")
            
        except Exception as e:
            print(f"更新 {code} 失敗: {e}")

# 更新頂部的「時間標籤」
info_el = soup.find("span", id="market-update-info")
if info_el:
    import datetime
    today_str = datetime.datetime.now().strftime("%Y/%m/%d")
    info_el.string = f"📅 {today_str} 收盤資料 · 點擊看詳情"

# 儲存更新後的 HTML
with open(html_filename, "w", encoding="utf-8") as f:
    f.write(str(soup))

print("網頁更新完成！")