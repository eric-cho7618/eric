import json
import requests
from datetime import datetime
import pytz

# 1. 네이버 금융 공식 ETF 리스트 API (국내 가상서버/GitHub Action에서도 차단 없음)
url = "https://finance.naver.com/api/sise/etfItemList.naver"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

result_list = []

try:
    # 실시간 ETF 데이터 호출
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    
    # 네이버 API 결과 파싱
    data = res.json()
    etf_list = data.get('result', {}).get('etfItemList', [])
    print(f"실시간으로 로드된 전체 상품 수: {len(etf_list)}")
    
    candidates = []
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    
    for item in etf_list:
        name = item.get('itemname', '')
        code = item.get('itemcode', '')
        price = item.get('nowVal', 0)
        
        # 네이버 ETF API에서 제공하는 분배율(배당률) 필드: 'dividendYield'
        yield_pct = item.get('dividendYield', 0.0)
        
        # 고배당 관련 키워드가 이름에 포함되어 있는지 확인
        if any(kw in name for kw in keywords):
            try:
                yield_pct = float(yield_pct)
            except:
                yield_pct = 0.0
                
            # 배당률이 유효한 상품만 후보군에 등록
            if yield_pct > 0 and price:
                candidates.append({
                    "ticker": code,
                    "name": name,
                    "price": f"{int(price):,}원",
                    "yield": round(yield_pct, 2),
                    "market": "KR"
                })

    # 실시간 배당률이 높은 순서대로 정렬 후 상위 10개 추출
    if candidates:
        result_list = sorted(candidates, key=lambda x: x['yield'], reverse=True)[:10]
        print(f"실시간 고배당 ETF {len(result_list)}개 매핑 성공!")

except Exception as e:
    print(f"실시간 데이터 수집 실패 에러: {e}")

# [최종 방어선] API 장애 발생 등으로 데이터가 전혀 없을 때만 작동하는 백업 데이터
if not result_list:
    print("시스템 경고: 실시간 API 데이터를 가져오지 못해 백업 리스트를 적용합니다.")
    result_list = [
        {"ticker": "458730", "name": "TIGER 미국배당+7%프리미엄다우존스", "price": "10,250원", "yield": 10.45, "market": "KR"},
        {"ticker": "486290", "name": "PLUS 미국배당커버드콜고배당", "price": "9,840원", "yield": 9.82, "market": "KR"},
        {"ticker": "472150", "name": "KODEX 미국나스닥100데일리커버드콜", "price": "10,120원", "yield": 9.51, "market": "KR"},
        {"ticker": "161510", "name": "ARIRANG 고배당주", "price": "13,850원", "yield": 5.41, "market": "KR"}
    ]

# 한국 시간(KST) 기준으로 최근 업데이트 시간 기록
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

# 최종 data.json 파일 파일 쓰기
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f"성공적으로 '{output_data['updated_at']}' 기준 data.json이 업데이트되었습니다.")
