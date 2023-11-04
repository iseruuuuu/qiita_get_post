import time
import argparse
import requests
import json
from tabulate import tabulate
from tqdm import tqdm
from datetime import datetime
from zoneinfo import ZoneInfo

# メンバー全員の投稿アカウント毎の個人トークンの定義
tokens = {
    "iseki": "",
}

# https のパラメータ情報
params = {
    "page": "1",
    "per_page": "100",
}

# カットオフ日付をタイムゾーン付きで設定
cutoff_date = datetime(2022, 11, 1, tzinfo=ZoneInfo("Asia/Tokyo"))

# アカウント毎に投稿した記事のListを取得
def GetPostList():
    post_count = 0
    posts_since_cutoff = 0
    posts_before_cutoff = 0
    
    for account_name, token in tokens.items():
        print(f"\n ■---■---■ 投稿者：{account_name}")
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get('https://qiita.com/api/v2/authenticated_user/items', params=params, headers=headers)
        posts = json.loads(response.text)

        # 投稿記事毎View数の取得
        count, since, before = GetView(posts, headers)
        post_count += count
        posts_since_cutoff += since
        posts_before_cutoff += before

    return post_count, posts_since_cutoff, posts_before_cutoff


# 投稿した記事のView数の取得
def GetView(post_list, headers):
    # 取得する情報のキーと値の準備
    item_keys = ['User', 'url', 'page_views_count', 'likes_count', 'created_at', 'updated_at', 'Title']
    item_values = []

    posts_since_cutoff = 0
    posts_before_cutoff = 0

    # 投稿記事毎の情報の取得
    for item in tqdm(post_list):
        response = requests.get(f'https://qiita.com/api/v2/items/{item["id"]}', headers=headers)
        post = json.loads(response.text)

        # タイムゾーン付きのdatetimeオブジェクトへの変換
        created_at = datetime.fromisoformat(post['created_at'].rstrip('Z'))

        if created_at >= cutoff_date:
            posts_since_cutoff += 1
        else:
            posts_before_cutoff += 1

        item_values.append([
            post['user']['id'],
            post['url'],
            post['page_views_count'],
            post['likes_count'],
            post['created_at'],
            post['updated_at'],
            post['title']
        ])

    rows = [dict(zip(item_keys, item)) for item in item_values]

    # 取得情報の表示
    print(tabulate(rows, headers='keys'))
    print(f"\n   ---> 投稿数：{len(rows)}\n")

    return len(rows), posts_since_cutoff, posts_before_cutoff


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Qiitaの投稿記事に対するView数を取得する')
    args = parser.parse_args()

    start = time.time()
    cnt, posts_since_cutoff, posts_before_cutoff = GetPostList()
    elapsed_time = time.time() - start

    print(f"\nQiita Post 総数 : {cnt}")
    print(f"2022年11月以降の投稿数: {posts_since_cutoff}")
    print(f"それ以前の投稿数: {posts_before_cutoff}")
    print(f"取得時間: {elapsed_time:.2f} [sec] \n")
