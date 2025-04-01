import openai
import pandas as pd
import json

openai.api_key = "xxx" #APIキーを入力

def analyze_with_gpt(content_text, taste_text):
    """
    content（レビュー本文）と taste（テイスト情報）を元に、
    GPT-4o-mini で 7W2H(※"Which"抜き) + ABC をタグ付けする。
    """
    
    # systemメッセージ: タグ定義と "none" は使わず空配列に、などを明示
    system_message = """
あなたは高度なテキスト解析を行うアシスタントです。
ユーザーがアップロードしたCSVの各行（レビュー）について、
7W2H（"Which" を除く: When, Where, Who, Why, How, How_much）と
ABC（Affect, Behavior, Cognition）のカテゴリを判定し、
必ずJSON形式で出力してください。

各フィールドは配列。該当なければ "[]" を返してください。
"none" という文字列は使わないでください。

カテゴリ定義:

1) 7W2H
- When: ["morning", "daytime", "night", "special_event"]
- Where: ["home", "restaurant_bar", "travel", "other_place"]
- Who: ["reviewer_self", "family", "friends", "partner", "other_who"]
- Why: ["celebration", "stress_relief", "everyday_consumption", "curiosity", "other_why"]
- How: ["hot", "cold", "room_temp", "with_meal", "other_how"]
- How_much: ["low_price", "mid_price", "high_price"]

2) ABC
- Affect: ["joy","surprise","relief","disappointment","other_affect"]
- Behavior: ["repeat_purchase","recommend_to_others","sns_share","other_behavior"]
- Cognition: ["taste_sweet","taste_dry","taste_acidic","taste_bitter",
              "aroma_fruity","aroma_rich","brand_rare","high_quality",
              "cost_performance","other_cognition"]

出力例:
{
  "When": [],
  "Where": [],
  "Who": [],
  "Why": [],
  "How": [],
  "How_much": [],
  "Affect": [],
  "Behavior": [],
  "Cognition": []
}
"""

    # userメッセージ: 実際のレビュー本文とテイスト情報を渡す
    user_message = f"""
以下のレビュー本文とテイスト情報を参考に、上記カテゴリを分析してください。

【レビュー本文】
{content_text}

【テイスト情報】
{taste_text}

出力はJSON形式のみで、以下のフィールドを含めてください:
{{
  "When": [],
  "Where": [],
  "Who": [],
  "Why": [],
  "How": [],
  "How_much": [],
  "Affect": [],
  "Behavior": [],
  "Cognition": []
}}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        max_tokens=1000,
        temperature=0.0
    )

    # ChatGPTの返答（JSON文字列想定）
    gpt_output = response["choices"][0]["message"]["content"]
    return gpt_output


def main():
    # CSV読み込み
    input_file = "Juyondai_filter.csv"
    df = pd.read_csv(input_file)

    # 今回は "Which" カラムを作らない
    new_columns = [
        "When","Where","Who","Why","How","How_much",
        "Affect","Behavior","Cognition"
    ]
    for col in new_columns:
        df[col] = ""

    for idx, row in df.iterrows():
        content_text = row.get("content", "")
        taste_text   = row.get("taste", "")

        # GPT-4o-miniに投げる
        gpt_result_str = analyze_with_gpt(content_text, taste_text)

        # JSONをパース
        try:
            gpt_dict = json.loads(gpt_result_str)

            # DataFrameに反映（配列をカンマ区切りの文字列に）
            for col in new_columns:
                val = gpt_dict.get(col, [])
                if isinstance(val, list):
                    df.at[idx, col] = ",".join(val)
                else:
                    # 万が一文字列だったらそのまま
                    df.at[idx, col] = val
        except json.JSONDecodeError:
            print(f"[ERROR] JSONデコード失敗: row={idx}\n{gpt_result_str}")

    # CSV出力
    output_file = "labeled_reviews.csv"
    df.to_csv(output_file, index=False)
    print(f"Done! See: {output_file}")


if __name__ == "__main__":
    main()
