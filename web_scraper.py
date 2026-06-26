import os
import json
import requests
import subprocess
from bs4 import BeautifulSoup
from datetime import datetime

# スクリプトが置かれているフォルダの絶対パスを取得 (基準パス)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ターゲットURL (Yahoo!ニュース トップ)
URL = "https://news.yahoo.co.jp/"
JSON_PATH = os.path.join(BASE_DIR, "news.json")
TXT_PATH = os.path.join(BASE_DIR, "news_summary.txt")

def git_push_news():
    # GitHub Actions上で実行されている場合は、Pythonスクリプト内でのGitプッシュをスキップしてActionsの機能に任せる
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("ℹ️ GitHub Actions環境を検知しました。スクリプト内でのGitプッシュをスキップし、ワークフローの処理に委ねます。")
        return

    print("GitHubへ自動プッシュ中...")
    cwd = BASE_DIR
    
    # もしローカルでの動作時にリポジトリ内にいない場合は、親フォルダか適したフォルダをGit作業フォルダとする
    if not os.path.exists(os.path.join(cwd, ".git")):
        parent_dir = os.path.dirname(cwd)
        if os.path.exists(os.path.join(parent_dir, ".git")):
            cwd = parent_dir
        else:
            print("❌ エラー: Gitリポジトリ（.git）が見つかりません。自動プッシュをスキップします。")
            return
        
    try:
        # news.json に変更（差分）があるか確認
        # cwdがリポジトリルートを指すように、news.jsonのパスを補正
        target_file = "news.json" if cwd == BASE_DIR else "profile-page/news.json"
        
        status = subprocess.run(
            ["git", "status", "--porcelain", target_file],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if not status.stdout.strip():
            print("ℹ️ ニュースデータに変更はありません。プッシュをスキップします。")
            return
            
        # Gitコマンドの連続実行
        print("Gitコマンドを実行中...")
        subprocess.run(["git", "add", target_file], cwd=cwd, check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update news.json via scraping"], cwd=cwd, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=cwd, check=True)
        print("✅ GitHubへの自動公開が完了しました！")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Gitの実行中にエラーが発生しました: {e}")

def scrape_yahoo_news():
    print(f"Yahoo!ニュース ({URL}) からトピックスを取得中...")
    
    # 1. サイトにリクエストを送り、HTMLを取得
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"ページの取得に失敗しました: {e}")
        return
        
    # 2. BeautifulSoupでHTMLをパース (解析)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 3. ニュースリンクの抽出 (pickupを含むaタグを狙い撃ち)
    news_links = soup.select('a[href*="/pickup/"]')
    
    if not news_links:
        print("ニュース記事が見つかりませんでした。HTMLの構造が変更された可能性があります。")
        return
        
    # 重複を排除してデータを整理
    seen_titles = set()
    summary_data = []
    
    for link in news_links:
        title = link.get_text().strip()
        url = link.get("href")
        
        if title and title not in seen_titles:
            seen_titles.add(title)
            if url.startswith("/"):
                url = "https://news.yahoo.co.jp" + url
            summary_data.append({"title": title, "url": url})
            
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 4-A. テキストファイル形式で保存 (ローカル保存用)
    output_lines = [
        "==================================================\n",
        f" 📰 Yahoo!ニュース 主要トピックス一覧 (取得日時: {current_time})\n",
        "==================================================\n\n"
    ]
    
    print("\n" + output_lines[0].strip())
    print(output_lines[1].strip())
    print(output_lines[2].strip())
    
    for i, item in enumerate(summary_data, 1):
        line = f"[{i}] {item['title']}\n    URL: {item['url']}\n"
        print(f"[{i}] {item['title']}")
        print(f"    URL: {item['url']}")
        output_lines.append(line + "\n")
        
    try:
        with open(TXT_PATH, "w", encoding="utf-8") as f:
            f.writelines(output_lines)
        print(f"\n✅ ローカル用テキストファイルを '{TXT_PATH}' に保存しました。")
    except Exception as e:
        print(f"テキストファイルの保存に失敗しました: {e}")
        
    # 4-B. JSON形式で保存 (ホームページ連携用)
    data_to_save = {
        "scrapedAt": current_time,
        "news": summary_data
    }
    
    try:
        # 保存先フォルダが存在しない場合は作成 (安全対策)
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
        
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"✅ ホームページ用JSONデータを '{JSON_PATH}' に保存しました。")
        
        # 5. 保存したJSONを自動的にGitHubへプッシュ公開
        git_push_news()
        
    except Exception as e:
        print(f"JSONデータの保存に失敗しました: {e}")

if __name__ == "__main__":
    scrape_yahoo_news()
