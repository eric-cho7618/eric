import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}

# ─────────────────────────────────────────────
# Step 1. 네이버 ETF 전체 리스트에서 배당 키워드 종목 수집
# ─────────────────────────────────────────────
def get_dividend_etf_list():
    url = "https://finance.naver.com/api/sise/etfItemList.naver"
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    data = res.json()
    etf_list = data.get('result', {}).get('etfItemList', [])
    print(f"전체 ETF 수: {len(etf_list)}")

    keywords = ['배당', '고배당', '커버드콜', '프리미엄', '타겟', 'DIVIDEND', 'Yield']
    filtered = [
        e for e in etf_list
        if any(kw in e.get('itemname', '') for kw in keywords)
    ]
    print(f"배당 키워드 ETF 수: {len(filtered)}")
    return filtered

# ─────────────────────────────────────────────
# Step 2. 네이버 ETF 상세 페이지에서 배당수익률 파싱
# ─────────────────────────────────────────────
def get_yield_from_naver(code):
    url = f"https://finance.naver.com/etf/etfProfile.naver?code={code}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 배당수익률 테이블에서 파싱
        # "분배율" 또는 "배당수익률" 텍스트 옆 값 찾기
        rows = soup.select('table.tb_compare tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                label = th.get_text(strip=True)
                if '분배율' in label or '배당수익률' in label or 'yield' in label.lower():
                    val = td.get_text(strip=True).replace('%', '').replace(',', '').strip()
                    try:
                        return float(val)
                    except:
                        pass

        # 대안: 분배금수익률 div 파싱
        for tag in soup.find_all(['td', 'dd', 'span']):
            text = tag.get_text(strip=True)
            if '%' in text:
                val = text.replace('%', '').strip()
                try:
                    v = float(val)
                    if 0.5 < v < 50:  # 합리적 배당률 범위
                        return v
                except:
                    pass
    except Exception as e:
        print(f"  [{code}] 파싱 오류: {e}")
    return 0.0

# ─────────────────────────────────────────────
# Step 3. KRX API로 현재가 보완 (네이버 nowVal 우선 사용)
# ─────────────────────────────────────────────
def get_etf_price(code, fallback_price):
    if fallback_price and fallback_price > 0:
        return f"{int(fallback_price):,}원"
    return "-"

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
result_list = []

try:
    filtered_etfs = get_dividend_etf_list()
    candidates = []

    for item in filtered_etfs:
        code = item.get('itemcode', '')
        name = item.get('itemname', '')
        price = item.get('nowVal', 0)

        if not code:
            continue

        yield_pct = get_yield_from_naver(code)
        time.sleep(0.3)  # 과도한 요청 방지

        if yield_pct <= 0:
            print(f"  [{code}] {name} → 배당률 없음, 스킵")
            continue

        candidates.append({
            "ticker": code,
            "name": name,
            "price": get_etf_price(code, price),
            "yield": round(yield_pct, 2),
            "market": "KR"
        })
        print(f"  [{code}] {name} → {yield_pct}%")

    result_list = sorted(candidates, key=lambda x: x['yield'], reverse=True)[:10]
    print(f"\n최종 TOP {len(result_list)}개 선정 완료")

except Exception as e:
    print(f"Error: {e}")

if not result_list:
    result_list = [{
        "ticker": "-",
        "name": "데이터를 일시적으로 가져올 수 없습니다.",
        "price": "-",
        "yield": 0.0,
        "market": "KR"
    }]

seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M:%S')

output_data = {"updated_at": now, "list": result_list}

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print("국내 상장 고배당 ETF TOP 10 수집 및 저장 완료!")
