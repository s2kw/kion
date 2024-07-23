import pandas as pd
import requests
import os
import json
import re
from io import StringIO

# 気象庁の最新気温データのURL
url = "https://www.data.jma.go.jp/stats/data/mdrr/tem_rct/alltable/mxtemsadext00_rct.csv"

# データを取得
response = requests.get(url)
response.encoding = 'shift_jis'  # 日本語文字コードの設定
data = StringIO(response.text)

# データをpandasデータフレームとして読み込み
df = pd.read_csv(data)

# データを保存 ローカルで確認する用
# file_path = "temperature_data.csv"
# df.to_csv(file_path, index=False)

# 特定の場所の気温を抽出
location = "東京（トウキョウ）"
temperature_data = df[df['地点'] == location]

# 指定時間の温度を取得
day=temperature_data['現在時刻(日)'].values[0]
temperature = temperature_data[f'{day}日の最高気温(℃)'].values[0]
print(f"{day}日の最高気温(℃): {temperature}")

# 取得タイミング
timing=f'{temperature_data['現在時刻(年)'].values[0]}年{temperature_data['現在時刻(月)'].values[0]}月{temperature_data['現在時刻(日)'].values[0]}日{temperature_data['現在時刻(時)'].values[0]}時{temperature_data['現在時刻(分)'].values[0]}分 計測'
temperature_info=f'{temperature}度@{timing}'
print(temperature_info)

# ジャッジ
judgement_temperature=28.0


# テキストの整形
comment=''
if temperature > 30:
    comment = "本日は在宅作業ですが熱中症には注意しましょう！"
elif temperature > judgement_temperature:
    comment = "本日は暑すぎるので在宅作業にしましょう！💀💀💀"
else:
    comment = "本日は残念ながら出社です。熱中症に気をつけて出社しましょう。😇😇😇"


# 特殊文字除去関数
def clean_text(text):
    # 正規表現を使用して、可視文字以外のすべての文字を除去
    # cleaned_text = re.sub(r'[^\u0020-\u007E\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]', '', text)
    
    # 通常の改行は残す 
    cleaned_text = re.sub(r'[^\u0020-\u007E\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\n\r]', '', text)
    return cleaned_text

# 天気予報も取得する
url = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/130000.json"
weather_info = ""
try:
    # URLからデータを取得
    response = requests.get(url)
    response.raise_for_status()  # エラーがあれば例外を発生させる
    
    # JSONデータをPythonオブジェクトに変換
    weather_data = json.loads(response.text)

    # 必要な情報を抽出
    publishing_office = weather_data['publishingOffice']
    report_datetime = weather_data['reportDatetime']
    target_area = weather_data['targetArea']
    headline_text = weather_data['headlineText']
    text = weather_data['text']
    
    def replace_multiple(text, replacements):
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    text = replace_multiple(text, {"\n\n":"\n"})

    # 天気予報情報を文字列変数に格納
    weather_info = f"発表元: {publishing_office}\n\n"
    weather_info += f"報告日時: {report_datetime}\n\n"
    weather_info += f"対象地域: {target_area}\n\n"
    weather_info += f"見出し: {headline_text}\n\n"
    weather_info += f"詳細:\n{clean_text(text)}"

    print(weather_info)

except requests.RequestException as e:
    print(f"エラーが発生しました: {e}")


# slack
slack_data = {'text': f"おはようございます🌞\n{comment}\n\n{temperature_info}\n\n{weather_info}" }

slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

response = requests.post(
    slack_webhook_url, json=slack_data,
    headers={'Content-Type': 'application/json'}
)


if response.status_code != 200:
    raise ValueError(
        f'Request to slack returned an error {response.status_code}, the response is:\n{response.text}'
    )
else:
    print("メッセージが送信されました。")


