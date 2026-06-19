import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}

# 1. 고배당 ETF 목록 가져오기
def get_dividend_etfs():
    url = "https://finance.naver.com/api/sise/etfItemList.naver"
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
    etf_list = data.get('result', {}).get('etfItemList', [])
    
    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    filtered = [e for e in etf_list if any(kw in e.get('itemname', '') for kw in keywords)]
    return filtered

# 2. 웹 페이지 파싱을 통해 최근 1년간 분배금 합산 가져오기
def get_annual_dividend(code):
    try:
        url = f"https://finance.naver.com/item/coinfo.naver?code={code}"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 주 주요재무정보 또는 배당 정보 테이블 탐색
        tables = soup.find_all('table')
        annual_div = 0
        
        # 네이버 분배금 내역 웹페이지 크롤링
        url_div = f"https://finance.naver.com/etf/etfDividendList.naver?etfCd={code}"
        res_div = requests.get(url_div, headers=headers, timeout=10)
        div_data = res_div.json()
        
        div_list = div_data.get('etfDividendList', [])
        if not div_list:
            return 0
            
        cutoff = datetime.now() - timedelta(days=365)
        for d in div_list:
            date_str = d.get('recordDate', '')
            amount = d.get('dividendPerUnit', 0) or 0
            try:
                dt = datetime.strptime(date_str, '%Y.%m.%d')
                if dt >= cutoff:
                    annual_div += int(amount)
            except:
                pass
        return annual_div
    except Exception as e:
        print(f"  [{code}] 분배금 수집 실패: {e}")
        return 0

# Main logic
result_list = []
try:
    etf_candidates = get_dividend_etfs()
    print(f"후보 ETF 수: {len(etf_candidates)}")
    
    # 안정적인 수집을 위해 상위 일부 후보만 타겟팅하여 수집 진행
    # 너무 많은 요청을 보내면 블락되므로 리스트 중 앞선 30개 종목에 대해 상세 검사
    count = 0
    for item in etf_candidates:
        if count >= 30: 
            break
            
        code = item.get('itemcode', '')
        name = item.get('itemname', '')
        price = item.get('nowVal', 0) or 0
        
        if not code: continue
        
        # 1년 분배금 직접 계산
        annual_div = get_annual_dividend(code)
        time.sleep(0.3) # 네이버 서버 보호용 디레이
        
        if annual_div > 0 and price > 0:
            yield_pct = round((annual_div / price) * 100, 2)
            result_list.append({
                "ticker": code,
                "name": name,
                "price": f"{int(price):,}원",
                "yield": yield_pct,
                "market": "KR"
            })
            print(f"  [{code}] {name} - 현재가: {price}원 / 연배당금: {annual_div}원 -> 배당률: {yield_pct}%")
            count += 1

    # 최종 배당수익률 순 정렬 후 TOP 10 선정
    result_list = sorted(result_list, key=lambda x: x['yield'], reverse=True)[:10]

except Exception as e:
    print(f"종합 에러 발생: {e}")

# 최종 방어용
if not result_list:
    result_list = [{"ticker": "-", "name": "유효한 배당 데이터를 찾지 못했습니다.", "price": "-", "yield": 0.0, "market": "KR"}]

seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')
output_data = {"updated_at": now, "list": result_list}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("모든 수집 및 갱신이 완료되었습니다.")
