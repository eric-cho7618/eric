import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# 네이버 증권 배당 수익률 상위 페이지 URL
url = "https://finance.naver.com/sise/dividend_list.naver"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

result_list = []

try:
    res = requests.get(url, headers=headers)
    # 네이버 증권은 EUK-KR(cp949) 인코딩을 사용하므로 한글 깨짐 방지 설정
    res.encoding = 'cp949' 
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 배당률 데이터가 있는 테이블 찾기
    table = soup.find('table', {'class': 'type_2'})
    if table:
        rows = table.find_all('tr')
        rank_count = 0
        
        for row in rows:
            # 상위 10개 종목만 수집하면 종료
            if rank_count >= 10:
                break
                
            tds = row.find_all('td')
            # 정상적인 데이터가 들어있는 행인지 확인 (열 개수가 충분한지)
            if len(tds) >= 7:
                name_td = tds[0].find('a')
                if name_td:
                    name = name_td.text.strip()
                    # 링크 주소에서 종목 코드(6자리) 추출
                    href = name_td.get('href', '')
                    code = href.split('code=')[-1] if 'code=' in href else '-'
                    
                    price = f"{tds[1].text.strip()}원" # 현재가
                    
                    # 네이버 배당 수익률 페이지 기준 (보통 5번째나 6번째 열에 배당수익률 위치)
                    # 구조에 안전하게 접근하기 위해 % 기호가 붙은 열을 찾거나 고정 인덱스 활용
                    try:
                        yield_text = tds[5].text.strip().replace(',', '')
                        yield_percent = float(yield_text)
                    except ValueError:
                        yield_percent = 0.0
                        
                    result_list.append({
                        "ticker": code,
                        "name": name,
                        "price": price,
                        "yield": yield_percent,
                        "market": "KR"
                    })
                    rank_count += 1

except Exception as e:
    print(f"Error fetching dividend top 10: {e}")

# 혹시 몰라 배당률 순으로 한 번 더 정렬
result_list = sorted(result_list, key=lambda x: x['yield'], reverse=True)

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

print("국내 고배당주 TOP 10 실시간 수집 및 저장 완료!")
