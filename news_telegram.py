import requests
import feedparser
import os
from datetime import datetime, timezone, timedelta

# =============================================
# 설정값 (GitHub Secrets에서 불러옴)
# =============================================
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")   # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") # 텔레그램 채팅 ID

# 수집할 종목 (종목명: 네이버 뉴스 검색어)
STOCKS = {
    "대한항공":  "대한항공",
    "한화오션":  "한화오션",
    "SK텔레콤": "SK텔레콤",
    "현대건설":  "현대건설",
}

# 네이버 뉴스 RSS URL
NAVER_RSS = "https://search.naver.com/rss?where=news&query={query}&sort=1"

# =============================================
# 텔레그램 메시지 전송
# =============================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, data=payload, timeout=10)
        if res.status_code == 200:
            print("텔레그램 전송 성공")
        else:
            print("텔레그램 전송 실패:", res.text)
    except Exception as e:
        print("텔레그램 오류:", e)

# =============================================
# 뉴스 수집 (최근 1시간 이내)
# =============================================
def fetch_news(stock_name, query):
    url = NAVER_RSS.format(query=requests.utils.quote(query))
    feed = feedparser.parse(url)

    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    cutoff = now - timedelta(hours=1)  # 최근 1시간

    news_list = []
    for entry in feed.entries[:10]:  # 최대 10개만 확인
        try:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(KST)
        except Exception:
            continue

        if pub >= cutoff:
            title = entry.title.replace("<b>", "").replace("</b>", "")
            news_list.append({
                "title": title,
                "link":  entry.link,
                "time":  pub.strftime("%H:%M"),
            })

    return news_list

# =============================================
# 메인 실행
# =============================================
def main():
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    now_str = now.strftime("%Y-%m-%d %H:%M")

    print(f"[{now_str}] 뉴스 수집 시작")

    all_messages = []

    for stock_name, query in STOCKS.items():
        news_list = fetch_news(stock_name, query)
        print(f"  {stock_name}: {len(news_list)}건")

        if news_list:
            lines = [f"<b>[{stock_name}] 최신 뉴스 ({now_str})</b>"]
            for i, n in enumerate(news_list, 1):
                lines.append(f"{i}. [{n['time']}] <a href='{n['link']}'>{n['title']}</a>")
            all_messages.append("\n".join(lines))

    if all_messages:
        for msg in all_messages:
            send_telegram(msg)
    else:
        print("최근 1시간 내 새 뉴스 없음 - 전송 건너뜀")

if __name__ == "__main__":
    main()
