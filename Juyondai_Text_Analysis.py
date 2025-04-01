import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import japanize_matplotlib
plt.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'

import urllib.request
import re
import MeCab
from wordcloud import WordCloud
from collections import Counter
from gensim import corpora
from gensim.models import LdaModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# =======================
# 1. 必要な準備・設定など
# =======================

def parse_japanese_date(date_string):
    """
    例: '2021年10月03日' → '2021-10-03' に変換する関数。
    """
    year, month, day = date_string.replace('年', ' ').replace('月', ' ').replace('日', '').split()
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

# MeCabの初期化
mecabrc = "/usr/local/etc/mecabrc"
neologd_dic = "/usr/local/lib/mecab/dic/mecab-ipadic-neologd"
m = MeCab.Tagger(f"-Ochasen -d {neologd_dic} -r {mecabrc}")

# -- 3.1 ストップワードの例 --
# ここではごく簡単に例として示していますが、実際はもっと充実したリストを用意してください
stopwords = set([
    'の', 'に', 'は', 'で', 'を', 'も', 'が', 'する', 
    'や', 'な', 'ない', 'いる', 'ある', 'こと', 'これ','甘い','旨い',
    '美味しい','水','感覚','詳細'
    # 必要に応じて追加 ...
])
# 分析対象とする品詞
target_parts_of_speech = [
    "名詞-サ変接続",
    "名詞-形容動詞語幹",
    "名詞-一般",
    "名詞-固有名詞-一般",
    "名詞-固有名詞-組織",
    "形容詞-自立"
]

# =======================
# 2. 前処理関数の定義
# =======================
def preprocess_text(text):
    """
    MeCabで形態素解析し、上記の品詞に合致＆ストップワード除去した単語を
    スペース区切りの文字列として返す。
    """
    lines = m.parse(text).splitlines()
    words = []
    for line in lines:
        parts = line.split('\t')
        # parts = ['表層形', '読み？', '原形？', '品詞細分類', ...] など
        if len(parts) > 3:
            # 品詞細分類を '-' で区切って必要な範囲を確認
            part_of_speech = parts[3].split('-')
            # 例: part_of_speech = ['名詞','一般'] → '-'.join(part_of_speech[:2]) = '名詞-一般'
            if '-'.join(part_of_speech[:2]) in target_parts_of_speech:
                word_surface = parts[0]
                if word_surface not in stopwords:
                    words.append(word_surface)
    return ' '.join(words)

df = pd.read_csv('/Users/tsuba/Desktop/juyondai_reviews.csv') #ファイル選択

# =======================
# 3. 前処理 (形態素解析)
# =======================
df['processed_text'] = df['content'].apply(preprocess_text)
print(df[['content', 'processed_text']])

# =======================
# 4. TF-IDFベクトル化
# =======================
vectorizer = TfidfVectorizer(
    max_df=0.8,   # 出現率80%以上の単語を無視する例
    min_df=1,     # 出現数1未満(=0)の単語は無視
    # tokenizerやpreprocessorは外部で済ませているので省略
)
X = vectorizer.fit_transform(df['processed_text'])

# 単語リスト
feature_names = vectorizer.get_feature_names_out()
print("語彙数:", len(feature_names), "次元")

# =======================
# 5. K-meansクラスタリング
# =======================
k = 5  # クラスタ数(適宜調整)
kmeans = KMeans(n_clusters=k, random_state=0, n_init='auto')
labels = kmeans.fit_predict(X)
df['cluster'] = labels
print("\n--- クラスタラベル ---")
print(df[['processed_text', 'cluster']])

# =======================
# 6. PCAで2次元可視化
# =======================
pca = PCA(n_components=2, random_state=0)
X_pca = pca.fit_transform(X.toarray())

plt.figure(figsize=(8, 6))
for cluster_id in range(k):
    # 各クラスタの点を描画
    cluster_points = X_pca[df['cluster'] == cluster_id]
    plt.scatter(cluster_points[:, 0], cluster_points[:, 1], label=f"Cluster {cluster_id}")

plt.title("K-means clustering of Sake Reviews (PCA)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.legend()
plt.show()

# =======================
# 7. クラスタの解釈
# =======================
# 7-1. クラスタ中心の上位単語を確認
centers = kmeans.cluster_centers_
topn = 5  # 上位5単語を表示

print("\n=== クラスタの上位単語 ===")
for cluster_id in range(k):
    # クラスタ中心ベクトル
    center_vec = centers[cluster_id]
    # 重みが大きい順に単語をソート
    top_indices = center_vec.argsort()[::-1][:topn]
    top_words = [(feature_names[i], center_vec[i]) for i in top_indices]
    
    print(f"\n[Cluster {cluster_id}]")
    for word, score in top_words:
        print(f" {word}: {score:.4f}")


# 7-2. WordCloudで可視化する場合 (各クラスタの単語をまとめる)
for cluster_id in range(k):
    cluster_texts = df.loc[df['cluster'] == cluster_id, 'processed_text']
    # 1つの文字列にまとめる
    cluster_words_all = " ".join(cluster_texts)
    
    # WordCloudの生成
    wordcloud = WordCloud(
        background_color="white",
        width=800,
        height=600,
        font_path="/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"  # 適宜フォントパス調整
    ).generate(cluster_words_all)
    
    plt.figure(figsize=(6,4))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"WordCloud for Cluster {cluster_id}")
    plt.show()
