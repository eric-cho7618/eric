import json
import requests
from datetime import datetime
import pytz

# 네이버 증권 ETF 실시간 전체 리스트 API
url = "https://finance.naver.com/api/sise/etfItemList.naver"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}

result_list = []

try:
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    data = res.json()
    
    etf_list = data.get('result', {}).get('etfItemList', [])
    print(f"전체 ETF 수: {len(etf_list)}")
    
    candidates = []
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    
    for item in etf_list:
        name = item.get('itemname', '')
        
        # 배당 관련 키워드가 포함된 ETF 필터링
        if any(kw in name for kw in keywords):
            code = item.get('itemcode', '')
            price = item.get('nowVal', 0) or 0
            
            # 네이버 ETF 기본 목록 API에서 제공하는 배당 수익률 항목 매핑
            # 주말이나 마감 직후 간혹 null인 경우를 방지하기 위해 안전하게 처리
            yield_pct = item.get('dividendYield')
            if yield_pct is None:
                yield_pct = 0.0
            else:
                try:
                    yield_pct = float(yield_pct)
                except:
                    yield_pct = 0.0
            
            # 배당률이 0보다 큰 유효한 종목만 후보에 등록
            if yield_pct > 0:
                candidates.append({
                    "ticker": code,
                    "name": name,
                    "price": f"{int(price):,}원" if price else "-",
                    "yield": yield_pct,
                    "market": "KR"
                })

    # 배당률이 높은 순서대로 정렬한 뒤 상위 10개만 선택
    result_list = sorted(candidates, key=lambda x: x['yield'], reverse=True)[:10]
    print(f"성공적으로 {len(result_list)}개의 고배당 ETF를 추출했습니다.")

except Exception as e:
    print(f"데이터 수집 에러: {e}")

# 만약 차단 등으로 인해 데이터가 아예 없을 경우의 방어 코드
if not result_list:
    result_list = [{
        "ticker": "-",
        "name": "데이터 수집 조건을 만족하는 ETF가 없습니다.",
        "price": "-",
        "yield": 0.0,
        "market": "KR"
    }]

# 한국 시간 기준으로 업데이트 시간 기록
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("국내 상장 고배당 ETF TOP 10 수집 및 저장 완료!")
