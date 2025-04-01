import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

base_url = "https://www.saketime.jp"
start_url = "https://www.saketime.jp/ranking/page:"

total_pages = 132

all_sake_data = []

def get_detail_page_info(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    description = soup.find('div', class_='mod-centerbox').find('p').text.strip() if soup.find('div', class_='mod-centerbox') else ""
    
    # 「〇〇を飲む人はこんなお酒も飲んでいます」の情報を取得
    related_sakes = []
    related_sake_section = soup.find('h4', text=lambda t: '飲む人はこんなお酒も飲んでいます' in t if t else False)
    if related_sake_section:
        related_sake_list = related_sake_section.find_next('ol', class_='ranking')
        if related_sake_list:
            for sake in related_sake_list.find_all('li', class_='clearfix')[:10]:  # 上位5つまで取得
                sake_name = sake.find('p', class_='pName').text.strip()
                sake_info = sake.find('p', class_='pSpec').text.strip()
                sake_score = sake.find('p', class_='point').text.strip()
                related_sakes.append(f"{sake_name} ({sake_info}) - {sake_score}")
    related_sakes_str = " | ".join(related_sakes)
    
    return description, related_sakes_str

for page in range(1, total_pages + 1):
    try:
        url = f"{start_url}{page}/"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        ranking_items = soup.find_all('li', class_='clearfix')
        for item in ranking_items:
            try:
                rank_element = item.find('p', class_=lambda x: x and 'rank-' in x)
                if not rank_element:
                    rank_element = item.find('p', class_='rank-100')
                rank = rank_element.text.strip() if rank_element else ""

                name_element = item.find('h2')
                detail_url = base_url + name_element.find('a')['href'] if name_element and name_element.find('a') else ""

                if detail_url:
                    name = name_element.text.strip()
                    kana = item.find('h2').find('a').next_sibling.strip().strip('（）')
                    
                    brand_info = item.find('p', class_='brand_info')
                    prefecture, brewery = brand_info.text.strip().split(' | ') if brand_info else ("", "")
                    
                    rating_element = item.find('span', class_='point')
                    rating = rating_element.text.strip() if rating_element else ""
                    
                    review_count_element = item.find('span', text=lambda t: t and '件' in t)
                    review_count = review_count_element.text.strip('()') if review_count_element else ""
                    
                    price_range_element = item.find('p', class_='brand_price')
                    price_range = price_range_element.text.strip().replace('通販価格帯：', '').replace('～', '-') if price_range_element else ""
                    
                    description, related_sakes_str = get_detail_page_info(detail_url)
                    
                    all_sake_data.append([rank, name, kana, prefecture, brewery, rating, review_count, price_range, description, related_sakes_str])

                time.sleep(0.25)

            except Exception as e:
                print(f"Error processing item on page {page}: {e}")
                continue

        print(f"Page {page} processed successfully.")

    except Exception as e:
        print(f"Error processing page {page}: {e}")
        continue

df = pd.DataFrame(all_sake_data, columns=['順位', '銘柄名', '読み方', '都道府県', '蔵元', '評価', 'レビュー数', '価格帯', '説明', '関連銘柄'])

# すべての列の文字列データから改行と前後の空白を削除
for column in df.columns:
    df[column] = df[column].astype(str).str.replace('\n', ' ').str.strip()

# CSVファイルとして保存（フィールドをダブルクォーテーションで囲む）
df.to_csv('sake_ranking.csv', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

print("CSVファイルが作成されました: sake_ranking.csv")
