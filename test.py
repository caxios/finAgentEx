import yfinance as yf
import undetected_chromedriver as uc
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

data = yf.Ticker('AAPL').get_news(count=100)

news_list = [
    {
        "title": item['content']['title'],
        "summary": item['content']['summary'],
        "pubDate": item['content']['pubDate'][:10],
        "url": item['content']['clickThroughUrl']['url'] if item['content']['clickThroughUrl'] else None
    }
    for item in data[:20]
    if 'content' in item
]

url = news_list[0]['url']


# 옵션 설정
options = uc.ChromeOptions()
# options.add_argument('--headless') # 필요하면 주석 해제 (화면 안 보임)

print("브라우저를 실행합니다 (봇 탐지 우회 모드)...")
# version_main은 본인 크롬 버전에 맞춰주면 좋지만, 보통 안 적어도 알아서 잡습니다.
driver = uc.Chrome(options=options, use_subprocess=True)

try:
    driver.get(url)
    
    # 사람이 들어간 것처럼 3~5초 정도 여유 있게 기다려줍니다.
    print("페이지 로딩 대기 중...")
    time.sleep(random.uniform(4, 6)) # 랜덤하게 쉬면 더 사람 같습니다.
    
    # HTML 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. 본문 찾기 시도 (가장 흔한 클래스)
    article = soup.find('div', class_='caas-body')
    
    # 2. 만약 못 찾으면 다른 클래스 이름으로도 시도 (야후 뉴스 레이아웃이 2가지임)
    if not article:
        article = soup.find('div', class_='ymap-container-body')

    if article:
        print("-" * 50)
        print("★ 성공! 봇 탐지를 뚫었습니다.")
        print("본문 내용 일부:")
        print(article.get_text(strip=True))
        print("-" * 50)
    else:
        print("여전히 'Oops'가 뜨거나 본문을 못 찾았습니다.")
        # 디버깅: 제목이라도 제대로 떴는지 확인
        title = soup.find('h1')
        print(f"현재 페이지 제목: {title.get_text(strip=True) if title else '제목 없음'}")

except Exception as e:
    print(f"에러 발생: {e}")

finally:
    driver.quit()
    print("종료")