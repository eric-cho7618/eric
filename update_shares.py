import yfinance as yf
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# 1. 미국 주식 및 ETF 티커 리스트
us_tickers = ["JEPI", "JEPQ", "O", "MAIN"]

# 2. 한국 주식 종목 코드 리스트 (원하는 종목을 계속 추가할 수 있습니다)
kr_tickers = {
    "088980": "맥쿼리인프라",
    "005935": "삼성전자우",
    "379800": "KINDEX 미국고배당S&P"
}

result_list = []

# --- [미국 주식 수집] ---
for ticker_symbol in us_tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        dividend_yield = info.get('dividendYield', 0)
        yield_percent = round(dividend_yield * 100, 2) if dividend_yield else 0
        name = info.get('shortName', ticker_symbol)

        result_list.append({
            "ticker": ticker_symbol,
            "name": name,
            "price": f"${price}" if price else "-",
            "yield": yield_percent,
            "market": "US"
        })
    except Exception as e:
        print(f"Error fetching US {ticker_symbol}: {e}")

# --- [한국 주식 수집 (네이버 증권)] ---
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

for code, default_name in kr_tickers.items():
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. 현재가 추출
        price = "-"
        today_div = soup.find('div', {'class': 'today'})
        if today_div:
            blind_span = today_div.find('span', {'class': 'blind'})
            if blind_span:
                price = f"{blind_span.text.strip()}원"
        
        # 2. 배당수익률 추출
        yield_percent = 0.0
        # 종목 분석 영역 텍스트를 찾아서 배당수익률 파싱
        aside = soup.find('div', {'id': 'aside'})
        if aside:
            encorp_info = aside.find('div', {'class': 'encorp_info'})
            if encorp_info:
                # 테이블 내부의 모든 행을 검사
                for tr in encorp_info.find_all('tr'):
                    if '배당수익률' in tr.text:
                        th_or_td = tr.find('td') or tr.find('em')
                        if th_or_td:
                            val_text = th_or_td.text.strip().replace('%', '').replace(',', '')
                            try:
                                yield_percent = float(val_text)
                            except ValueError:
                                yield_percent = 0.0
                        break
                        
        result_list.append({
            "ticker": code,
            "name": default_name,
            "price": price,
            "yield": yield_percent,
            "market": "KR"
        })
    except Exception as e:
        print(f"Error fetching KR {code}: {e}")

# 배당률이 높은 순서대로 정렬
result_list = sorted(result_list, key=lambda x: x['yield'], reverse=True)

# 한국 시간 기준으로 업데이트 시간 기록
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

# 최종 파일 저장 (오류가 나더라도 구조가 깨지지 않도록 보장)
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("안전하게 데이터 수집 및 data.json 저장 완료!")
