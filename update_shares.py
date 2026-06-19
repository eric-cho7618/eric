import json
import requests
import yfinance as yf
from datetime import datetime
import pytz

# 네이버 증권 ETF 전체 리스트 API
url = "https://finance.naver.com/api/sise/etfItemList.naver"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

result_list = []

try:
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    data = res.json()

    etf_list = data.get('result', {}).get('etfItemList', [])
    print(f"전체 ETF 수: {len(etf_list)}")

    # 고배당 관련 키워드 필터링
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    dividend_etfs = [
        item for item in etf_list
        if any(kw in item.get('itemname', '') for kw in keywords)
    ]
    print(f"배당 키워드 ETF 수: {len(dividend_etfs)}")

    result_candidates = []

    for item in dividend_etfs:
        code = item.get('itemcode', '')
        name = item.get('itemname', '')
        price = item.get('nowVal', 0)

        if not code:
            continue

        # yfinance로 배당률 조회 (KRX 종목은 {code}.KS)
        try:
            ticker = yf.Ticker(f"{code}.KS")
            info = ticker.info
            # dividendYield는 소수 (예: 0.08 = 8%), 없으면 0
            raw_yield = info.get('dividendYield') or info.get('yield') or 0.0
            yield_percent = round(float(raw_yield) * 100, 2)
        except Exception as e:
            print(f"  [{code}] yfinance 오류: {e}")
            yield_percent = 0.0

        if yield_percent <= 0:
            continue

        result_candidates.append({
            "ticker": code,
            "name": name,
            "price": f"{int(price):,}원" if price else "-",
            "yield": yield_percent,
            "market": "KR"
        })
        print(f"  [{code}] {name} → {yield_percent}%")

    # 배당률 높은 순 TOP 10
    result_list = sorted(result_candidates, key=lambda x: x['yield'], reverse=True)[:10]
    print(f"최종 TOP {len(result_list)}개 선정 완료")

except Exception as e:
    print(f"Error: {e}")

# 데이터 없을 경우 방어 처리
if not result_list:
    result_list = [{
        "ticker": "-",
        "name": "데이터를 일시적으로 가져올 수 없습니다.",
        "price": "-",
        "yield": 0.0,
        "market": "KR"
    }]

# 한국 시간 기준 업데이트 시각
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("국내 상장 고배당 ETF TOP 10 수집 및 저장 완료!")
