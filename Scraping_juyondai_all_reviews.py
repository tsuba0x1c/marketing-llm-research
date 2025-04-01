import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

base_url = "https://www.saketime.jp/brands/241/page:"

def get_reviews(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    reviews = []
    review_elements = soup.find_all('li', class_='wrap clearfix')
    for review in review_elements:
        reviewer = review.find('h3').text.strip() if review.find('h3') else ""
        rating = review.find('span', class_='review_point').text.strip() if review.find('span', class_='review_point') else ""
        date = review.find('p', class_='r-date').find('span').text.strip() if review.find('p', class_='r-date') else ""
        content = review.find('p', class_='r-body').text.strip() if review.find('p', class_='r-body') else ""
        
        taste_info = review.find('div', class_='reviewSpecInfo')
        if taste_info:
            taste_elements = taste_info.find_all('p', class_='clearfix')
            taste = ' '.join([elem.text.strip().replace('\n', ' ') for elem in taste_elements])
        else:
            taste = ""
        
        reviews.append({
            'brand_name': "十四代",
            'reviewer': reviewer,
            'rating': rating,
            'date': date,
            'content': content,
            'taste': taste
        })
    
    return reviews, soup

def get_total_pages(soup):
    pagination = soup.find('div', class_='pagination')
    if pagination:
        page_links = pagination.find_all('a')
        if page_links:
            last_page_link = page_links[-1]['href']
            return int(last_page_link.split(':')[-1])
    return 1

all_reviews = []
page = 1
total_pages = 236  # 既知の総ページ数

while page <= total_pages:
    url = f"{base_url}{page}"
    try:
        reviews, soup = get_reviews(url)
        all_reviews.extend(reviews)
        print(f"Processed page {page} of {total_pages}")

        page += 1
        time.sleep(0.5)  # サーバーに負荷をかけないよう0.5秒待機
    except Exception as e:
        print(f"Error processing page {page}: {e}")
        break

# レビューデータをCSVファイルとして保存
df_reviews = pd.DataFrame(all_reviews)

# すべての列の文字列データから改行と前後の空白を削除
for column in df_reviews.columns:
    df_reviews[column] = df_reviews[column].astype(str).str.replace('\n', ' ').str.strip()

df_reviews.to_csv('juyondai_all_reviews.csv', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

print(f"十四代の全レビューデータのCSVファイルが作成されました: juyondai_all_reviews.csv (総レビュー数: {len(all_reviews)})")
