import json
import requests
from datetime import datetime
import pytz
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/'
}

# ─────────────────────────────────────────────
# Step 1. 네이버 ETF 전체 리스트 + 현재가 수집
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
# Step 2. 네이버 ETF 분배금 API로 연간 배당률 계산
#   /etf/etfDividendList.naver?etfCd={code}
#   → 최근 12개월 분배금 합산 / 현재가 * 100
# ─────────────────────────────────────────────
def get_yield_from_dividend_api(code, current_price):
    if not current_price or current_price <= 0:
        return 0.0
    try:
        url = f"https://finance.naver.com/etf/etfDividendList.naver?etfCd={code}"
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        # 응답 구조: {"etfDividendList": [{"dividendPerUnit": 숫자, "recordDate": "YYYY.MM.DD"}, ...]}
        div_list = data.get('etfDividendList', [])
        if not div_list:
            return 0.0

        # 최근 12개월 분배금 합산
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=365)
        annual_div = 0.0
        for d in div_list:
            date_str = d.get('recordDate', '')
            amount = d.get('dividendPerUnit', 0) or 0
            try:
                dt = datetime.strptime(date_str, '%Y.%m.%d')
                if dt >= cutoff:
                    annual_div += float(amount)
            except:
                pass

        if annual_div <= 0:
            return 0.0

        yield_pct = round(annual_div / current_price * 100, 2)
        return yield_pct

    except Exception as e:
        print(f"  [{code}] 분배금 API 오류: {e}")
        return 0.0

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
        price = item.get('nowVal', 0) or 0

        if not code:
            continue

        yield_pct = get_yield_from_dividend_api(code, price)
        time.sleep(0.2)

        if yield_pct <= 0:
            continue

        candidates.append({
            "ticker": code,
            "name": name,
            "price": f"{int(price):,}원" if price else "-",
            "yield": yield_pct,
            "market": "KR"
        })
        print(f"  [{code}] {name} → {yield_pct}%")

    result_list = sorted(candidates, key=lambda x: x['yield'], reverse=True)[:10]
    print(f"\n최종 TOP {len(result_list)}개 선정 완료")

except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()

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
