import yfinance as yf
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# 1. 미국 주식 및 ETF 티커 리스트
us_tickers = ["JEPI", "JEPQ", "O", "MAIN"]

# 2. 한국 주식 종목 코드 리스트 (예시: 맥쿼리인프라, 삼성전자우 등)
# 보고 싶으신 한국 종목의 6자리 코드를 추가하시면 됩니다.
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
            "price": f"${price}",  # 달러 표시
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
        
        # 현재가 추출
        today_div = soup.find('div', {'class': 'today'})
        price_text = today_div.find('span', {'class': 'blind'}).text if today_div else "0"
        price = price_text.strip()
        
        # 배당수익률 추출
        yield_percent = 0.0
        tbody = soup.find('table', {'summary': '주요재무정보 기업실적분석 제공'})
        if tbody:
            # 네이버 재무제표 테이블에서 가장 최근 배당수익률(%) 항목 찾기
            rows = tbody.find_all('tr')
            for row in rows:
                if '배당수익률' in row.text:
                    tds = row.find_all('td')
                    # 최근 결산 혹은 예상 배당률 중 가장 오른쪽에 있는 유효한 값 선택
                    for td in reversed(tds):
                        val = td.text.strip().replace(',', '')
                        if val and val != '-':
                            yield_percent = float(val)
                            break
                    break
        
        result_list.append({
            "ticker": code,
            "name": default_name,
            "price": f"{price}원",  # 원화 표시
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

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("국내/해외 배당 데이터 합산 및 저장 완료!")
