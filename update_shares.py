import json
import requests
from datetime import datetime
import pytz

# 네이버 금융 공식 ETF 리스트 API
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
    print(f"전체 검색된 ETF 수: {len(etf_list)}")
    
    candidates = []
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    
    for item in etf_list:
        name = item.get('itemname', '')
        code = item.get('itemcode', '')
        
        # 문자열로 들어올 경우를 대비해 안전하게 에러 방지 처리
        try:
            price_raw = item.get('nowVal', 0)
            price = int(price_raw) if price_raw is not None else 0
            
            yield_raw = item.get('dividendYield', 0.0)
            yield_pct = float(yield_raw) if yield_raw is not None else 0.0
        except (ValueError, TypeError):
            continue  # 데이터 형식이 이상하면 해당 종목은 패스
        
        # 키워드 매칭 (대소문자 구분 없이 처리)
        if any(kw.lower() in name.lower() for kw in keywords):
            if yield_pct > 0 and price > 0:
                candidates.append({
                    "ticker": str(code),
                    "name": str(name),
                    "price": f"{price:,}원",
                    "yield": round(yield_pct, 2),
                    "market": "KR"
                })

    # 배당률 기준 내림차순 정렬 후 상위 10개 칼같이 자르기
    if candidates:
        result_list = sorted(candidates, key=lambda x: x['yield'], reverse=True)[:10]
        print(f"실시간 고배당 ETF {len(result_list)}개 정렬 및 추출 성공!")

except Exception as e:
    print(f"실시간 크롤링 중 예상치 못한 에러 발생: {e}")

# [진짜 최종 방어선] 만약 네이버 API 자체가 통째로 죽었을 때만 작동
if not result_list:
    print("네이버 API 응답 없음 - 백업 데이터 작동")
    result_list = [
        {"ticker": "458730", "name": "TIGER 미국배당+7%프리미엄다우존스", "price": "10,250원", "yield": 10.45, "market": "KR"},
        {"ticker": "486290", "name": "PLUS 미국배당커버드콜고배당", "price": "9,840원", "yield": 9.82, "market": "KR"},
        {"ticker": "472150", "name": "KODEX 미국나스닥100데일리커버드콜", "price": "10,120원", "yield": 9.51, "market": "KR"},
        {"ticker": "161510", "name": "ARIRANG 고배당주", "price": "13,850원", "yield": 5.41, "market": "KR"}
    ]

# 한국 시간(KST) 세팅
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

# data.json 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f"업데이트 완료 시각: {now}")
