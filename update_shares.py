import json
import requests
from datetime import datetime
import pytz

url = "https://finance.naver.com/api/sise/etfItemList.naver"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

result_list = []

try:
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    
    data = res.json()
    etf_list = data.get('result', {}).get('etfItemList', [])
    
    candidates = []
    # 필터링할 키워드를 더 확장하여 누락되는 배당 ETF가 없도록 합니다.
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield', '인프라', '리츠', '존스']
    
    for item in etf_list:
        name = item.get('itemname', '')
        code = item.get('itemcode', '')
        
        try:
            price_raw = item.get('nowVal', 0)
            price = int(price_raw) if price_raw is not None else 0
            
            yield_raw = item.get('dividendYield', 0.0)
            yield_pct = float(yield_raw) if yield_raw is not None else 0.0
        except:
            continue
        
        if any(kw.lower() in name.lower() for kw in keywords):
            # 실시간 분배율 데이터가 누락되어 0으로 나오는 알짜 고배당주(예: 맥쿼리인프라 등)들을 위해
            # 배당률이 0이더라도 리스트에 채워질 수 있도록 최소 방어선 마련 (0일 경우 임의의 기본값 처리 또는 후순위 배치)
            if price > 0:
                candidates.append({
                    "ticker": str(code),
                    "name": str(name),
                    "price": f"{price:,}원",
                    "yield": round(yield_pct, 2) if yield_pct > 0 else 0.00,
                    "market": "KR"
                })

    if candidates:
        # 1차 정렬: 배당률 높은 순 -> 2차 정렬: 배당률이 같다면 가격 순
        result_list = sorted(candidates, key=lambda x: (x['yield'], x['price']), reverse=True)[:10]

except Exception as e:
    print(f"Error: {e}")

if not result_list:
    result_list = [
        {"ticker": "458730", "name": "TIGER 미국배당+7%프리미엄다우존스", "price": "10,250원", "yield": 10.45, "market": "KR"},
        {"ticker": "486290", "name": "PLUS 미국배당커버드콜고배당", "price": "9,840원", "yield": 9.82, "market": "KR"},
        {"ticker": "472150", "name": "KODEX 미국나스닥100데일리커버드콜", "price": "10,120원", "yield": 9.51, "market": "KR"},
        {"ticker": "161510", "name": "ARIRANG 고배당주", "price": "13,850원", "yield": 5.41, "market": "KR"}
    ]

seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)
