import yfinance as yf
import json
from datetime import datetime
import pytz

# 수집하고 싶은 고배당 주식 및 ETF 티커 리스트 (원하는 대로 추가 가능)
tickers = ["JEPI", "JEPQ", "O", "MAIN", "ARCC", "AGNC", "STAG", "SPHY", "TLTW"]

result_list = []

for ticker_symbol in tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 현재가 및 배당률 가져오기
        price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        dividend_yield = info.get('dividendYield', 0)
        
        # dividendYield가 소수점 형태(예: 0.07)이므로 100을 곱해 %로 변환
        yield_percent = round(dividend_yield * 100, 2) if dividend_yield else 0
        name = info.get('shortName', ticker_symbol)

        result_list.append({
            "ticker": ticker_symbol,
            "name": name,
            "price": price,
            "yield": yield_percent
        })
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")

# 배당률이 높은 순서대로 정렬
result_list = sorted(result_list, key=lambda x: x['yield'], reverse=True)

# 한국 시간 기준으로 업데이트 시간 기록
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

# JSON 파일로 저장
output_data = {
    "updated_at": now,
    "list": result_list
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("데이터 수집 및 data.json 저장 완료!")
