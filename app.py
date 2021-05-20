import sys
import os

import pyocr
import pyocr.builders

import difflib
import numpy as np
import pandas as pd

from PIL import Image

import streamlit as st

TESSERACT_PATH = 'C:\\Program Files\\Tesseract-OCR'
TESSDATA_PATH = 'C:\\Program Files\\Tesseract-OCR\\tessdata'

os.environ["PATH"] += os.pathsep + TESSERACT_PATH
os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH

csv_file = "result.csv"

capture_list = [(280, 380, 995, 440), (280, 588, 995, 648), (280, 797, 995, 857), (280, 1005, 995, 1065), (280, 1214, 995, 1274), (280, 1423, 995, 1483), (280, 1632, 995, 1692), (280, 1840, 995, 1900)]

char_list = ["カレンチャン", "サクラバクシンオー", "キングヘイロー", "ダイワスカーレット", "ウオッカ", "グラスワンダー", "アグネスタキオン", "ミホノブルボン", "ナリタタイシン", "ゴールドシップ", "メジロマックイーン", "スペシャルウィーク", "タイキシャトル", "エルコンドルパサー", "マルゼンスキー", "スマートファルコン", "トウカイテイオー", "エアグルーヴ", "マヤノトップガン", "ライスシャワー", "ウイニングチケット", "ナイスネイチャ", "メジロライアン", "スーパークリーク", "ハルウララ", "マチカネフクキタル", "オグリキャップ", "テイエムオペラオー", "ナリタブライアン", "シンボリルドルフ", "ビワハヤヒデ"]

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
# The tools are returned in the recommended order of usage
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))
# Ex: Will use tool 'libtesseract'
langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))
lang = langs[2]
print("Will use lang '%s'" % (lang))

# 画像ファイル読み込み
def read_image(dic, count_same_score, path):
    race_image = Image.open(path)
    # st.image(path)
    dic, count_same_score = update_dic(dic, race_image, count_same_score)

    return dic, count_same_score

# 文字列ならばchar_nameに、数字ならばscoreに。
def txt_arrange(txt):
    char = txt
    for i in txt:
        if i.isdigit():
            score = char.pop(char.index(i))
        else:
            pass
    char_name = ""
    for i in char:
        char_name += i

    return [char_name, score]

# 塗りつぶし処理。
def fill_mvp(im_capture):
    im_capture_info = np.array(im_capture)
    for col in range(60):
        for row in range(350, 471):
            im_capture_info[col][row] = im_capture_info[30][475]
    im_capture = Image.fromarray(im_capture_info)
    # im_capture.show()
    return im_capture

# 文字の読み取り、テキストの整形。
def read_text(im_capture):
    txt = tool.image_to_string(
        im_capture,
        lang=lang,
        builder=pyocr.builders.TextBuilder()
    )
    txt = txt.replace(".", "")
    txt = txt.replace(",", "")
    txt = txt.replace("pt", "")
    txt = txt.split()
    # print(txt)
    try:
        txt[1] = float(txt[1])
    except:
        txt = txt_arrange(txt)
        txt[1] = float(txt[1])

    # print(txt)

    return txt

# キャラ名の判別。
def judge_char_name(txt):
    hs = 0
    index = 0
    for j, char in enumerate(char_list):
        s = difflib.SequenceMatcher(None, txt[0], char).ratio()
        if s > hs:
            hs = s
            index = j
        else:
            pass

    txt[0] = char_list[index]

    return txt

# 辞書のスコアリストに写真から読み取ったスコアを追加。
def update_score(dic, txt, count_same_score):
    try:
        if txt[1] not in dic[txt[0]]:
            dic[txt[0]].append(txt[1])
        else:
            count_same_score += 1
            # print(count_same_score)
            if count_same_score > 2:
                print("最新のスコア情報と同じものです。")
                sys.exit()
            else:
                pass
    except KeyError:
        dic[txt[0]] = [txt[1]]
    except Exception as e:
        # print(f"エラー:{e}")
        print("line162 some error")
        dic[txt[0]].append(txt[1])

    return dic, count_same_score

def append_average(dic):
    try:
        for key in dic:
            ave = sum(dic[key])/len(dic[key])
            dic[key].append(round(ave, 1))
    except ZeroDivisionError:
        print("何かしらのデータがかけてるかも")
        ave = sum(dic[key])/len(dic[key])
        dic[key].append(round(ave, 1))

def update_dic(dic, image, count_same_score):
    for box in capture_list:
        im_capture = image.crop(box)
        im_capture = fill_mvp(im_capture)

        txt = read_text(im_capture)

        txt = judge_char_name(txt)

        dic, count_same_score = update_score(dic, txt, count_same_score)

    return dic, count_same_score

def dic_to_df(dic):
    char_index = []
    df_dic = {}
    for char in char_list:
        if char in dic:
            times = [f'第{i+1}レース' for i in range(len(dic[char]))]
            break
        else:
            pass
    for key in dic:
        df_dic[key] = []
    for key in dic:
        char_index.append(key)
        for score in dic[key]:
            df_dic[key].append(score)
    df = pd.DataFrame(
        df_dic, 
        index=times
    )
    df = df.T
    return df

def main():
    count_same_score = 0
    dic = {}
    append_average(dic)
    st.title('スコア分析')
    st.header('概要')
    st.write('写真をアップロードするとキャラ事にスコアの平均を出力します。')
    upload_file = st.file_uploader('ファイルのアップロード', accept_multiple_files=True)
    st.subheader('使用機種')
    option = st.selectbox('使用機種を選択してください', ('iPhoneSE', 'iPhone8', 'iPhone12'))
    st.write('選択中の言語：', option)

    if upload_file is not None:
        race_images = st.beta_expander('画像ファイル情報')
        race_images.write('ファイル詳細')
        for file in upload_file:
            content = file.read()
            file_details = {'FileName': file.name, 'FileType': file.type, 'FileSize': file.size}
            race_images.write(file_details)

        st.write('読み取り')
        if st.button('開始'):
            comment = st.empty()
            comment.write('集計を開始します')
            for file in upload_file:
                read_image(dic, count_same_score, file)
            append_average(dic)
            df = dic_to_df(dic)
            st.write(df)
            comment.write('完了しました')

if __name__ == "__main__":
    main()