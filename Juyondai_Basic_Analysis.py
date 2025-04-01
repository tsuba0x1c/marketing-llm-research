import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import japanize_matplotlib

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'
import urllib.request
import re
from wordcloud import WordCloud
from collections import Counter
from gensim import corpora
from gensim.models import LdaModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def parse_japanese_date(date_string):
    year, month, day = date_string.replace('年', ' ').replace('月', ' ').replace('日', '').split()
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

# データの読み込みと前処理
df = pd.read_csv('juyondai_all_reviews.csv')
df['date'] = df['date'].apply(parse_japanese_date)
df['date'] = pd.to_datetime(df['date'])
df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

# 1. 基本的な統計分析
average_rating = df['rating'].mean()
print(f"平均評価点: {average_rating:.2f}")

# 評価点の分布
plt.figure(figsize=(10, 6))
df['rating'].hist(bins=20)
plt.title('十四代の評価点分布')
plt.xlabel('評価点')
plt.ylabel('頻度')
plt.show()

# 時系列での評価点推移
df_monthly = df.groupby(df['date'].dt.to_period('M'))['rating'].mean()
plt.figure(figsize=(12, 6))
df_monthly.plot()
plt.title('十四代の月別平均評価点推移')
plt.xlabel('日付')
plt.ylabel('平均評価点')
plt.show()


# 評価点ごとの分布を集計
rating_distribution = df['rating'].value_counts().sort_index()

# 分布を表示
print("評価点ごとの分布:")
for rating, count in rating_distribution.items():
    print(f"評価点 {rating}: {count} 件")

# ヒストグラムをプロット
plt.figure(figsize=(10, 6))
rating_distribution.plot(kind='bar')
plt.title('評価点ごとの分布')
plt.xlabel('評価点')
plt.ylabel('頻度')
plt.xticks(rotation=0)
plt.show()
