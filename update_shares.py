import json
import requests
from datetime import datetime
import pytz

# 네이버 증권 ETF 실시간 전체 리스트 API (JSON 형태)
url = "https://finance.naver.com/api/sise/etfItemList.naver"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

result_list = []

try:
    res = requests.get(url, headers=headers)
    data = res.json()
    
    # ETF 전체 아이템 리스트 가져오기
    etf_list = data.get('result', {}).get('etfItemList', [])
    
    dividend_etfs = []
    
    for item in etf_list:
        name = item.get('itemname', '')
        # 고배당 관련 ETF 필터링 (배당, 고배당, 커버드콜, 프리미엄, 타겟 등)
        # 일반 개별 주식은 걸러지고 순수 배당형 ETF만 남습니다.
        if any(keyword in name for keyword in ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']):
            code = item.get('itemcode', '')
            price = item.get('nowVal', 0)
            
            # 네이버 ETF API에서 제공하는 배당수익률 값파싱
            # 없거나 0일 경우 추후 안전성 처리를 위해 수집
            yield_percent = item.get('dividendYield', 0.0)
            
            # 간혹 API에 배당률 분모가 누락되어 0으로 나오면 예외처리 타거나 하단 정렬에서 제외됨
            if yield_percent is None:
                yield_percent = 0.0
                
            dividend_etfs.append({
                "ticker": code,
                "name": name,
                "price": f"{price:,}원" if price else "-",
                "yield": float(yield_percent),
                "market": "KR"
            })

    # 배당률이 높은 순서대로 정렬한 뒤 상위 10개만 추출
    # 배당률 정보가 제공되지 않는(0.0%) 데이터는 우선 제외
    valid_etfs = [e for e in dividend_etfs if e['yield'] > 0]
    result_list = sorted(valid_etfs, key=lambda x: x['yield'], reverse=True)[:10]

except Exception as e:
    print(f"Error fetching dividend ETFs: {e}")

# 만약 API 점검 등으로 데이터가 하나도 안 뽑혔을 경우를 대비한 최소한의 방어 코드
if not result_list:
    result_list = [{"ticker": "-", "name": "데이터를 일시적으로 가져올 수 없습니다.", "price": "-", "yield": 0.0, "market": "KR"}]

# 한국 시간 기준으로 업데이트 시간 기록
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {
    "updated_at": now,
    "list": result_list
}

# 파일 저장
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("국내 상장 고배당 ETF TOP 10 수집 및 저장 완료!")
