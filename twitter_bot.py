import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

# 基準パスの取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_STATE_PATH = os.path.join(BASE_DIR, "auth_state.json")
NEWS_JSON_PATH = os.path.join(BASE_DIR, "news.json")

# 各種URL
WEATHER_URL = "https://weather.yahoo.co.jp/weather/jp/26/6110.html"
HOMEPAGE_URL = "https://yuppi-ai-studying.github.io/"

def get_weather_and_news(page):
    """Yahoo!天気とローカルJSONから、ツイート用のテキストを生成する"""
    print("🌐 天気予報データを取得中...")
    weather_text = "取得失敗"
    try:
        page.goto(WEATHER_URL)
        today_element = page.locator("#main .forecastCity > table > tbody > tr > td").first
        weather = today_element.locator("p.pict").inner_text().strip()
        high_temp = today_element.locator("li.high em").inner_text().strip()
        low_temp = today_element.locator("li.low em").inner_text().strip()
        weather_text = f"{weather} ({high_temp}℃/{low_temp}℃)"
    except Exception as e:
        print(f"⚠️ 天気データの取得に失敗しました: {e}")

    print("📖 ローカルのニュースデータを取得中...")
    news_title = "最新ニュースはありません"
    try:
        if os.path.exists(NEWS_JSON_PATH):
            with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("news"):
                    # 最初のニュースを取得
                    news_title = data["news"][0]["title"]
    except Exception as e:
        print(f"⚠️ ニュースデータの読み込みに失敗しました: {e}")

    # ツイートメッセージの組み立て (140文字制限に収まるように)
    message = (
        f"🌤️京都府南部の天気: {weather_text}\n\n"
        f"📰注目ニュース:\n・{news_title}\n\n"
        f"▼最新のニュース＆天気はこちら！\n{HOMEPAGE_URL}"
    )
    return message

def run_bot(message=None):
    # 1. ログイン状態（Cookie）の存在チェック
    if not os.path.exists(AUTH_STATE_PATH):
        print("🔑 ログインセッション情報 (auth_state.json) が見つかりません。")
        print("🌐 初回ログインセットアップを開始します...")
        print("📢 注意: ブラウザ画面が立ち上がりますので、ログインを完了させてください。")
        
        with sync_playwright() as p:
            # 初回は headless=False でブラウザを目視できるように起動
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
            # 一般的なデスクトップChromeのUser-Agentを偽装してコンテキストを作成
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            
            print("🌐 X (Twitter) のログイン画面を開いています...")
            page.goto("https://x.com/login")
            
            print("⏳ ログイン完了を待機しています (最大5分)...")
            try:
                # ログイン完了後、ホーム画面に遷移するのを監視します
                page.wait_for_url("**/home", timeout=300000)
                
                # 念のため、ホーム画面の特定の要素（サイドバーなど）が表示されるのを少し待つ
                page.wait_for_selector('a[href="/home"]', timeout=30000)
                
                print("✅ ログインを検知しました！セッション情報を保存しています...")
                context.storage_state(path=AUTH_STATE_PATH)
                print(f"💾 セッション情報を保存しました: {AUTH_STATE_PATH}")
                print("🎉 初回セットアップ完了です！ブラウザを終了します。")
                
            except Exception as e:
                print(f"❌ ログインの待機中にエラーが発生したか、制限時間を超過しました: {e}")
            finally:
                browser.close()
        return

    # 2. 自動投稿モード (Cookieがある場合)
    print("🤖 ログインセッションをロードして、自動投稿を開始します...")
    with sync_playwright() as p:
        # 2回目以降は本物のGoogle Chromeを headless=True で実行
        # (GitHub Actionsのクラウド上ではChromeアプリが入っていないため、デフォルト的のChromiumを使用)
        is_actions = os.environ.get("GITHUB_ACTIONS") == "true"
        browser = p.chromium.launch(
            headless=True,
            channel=None if is_actions else "chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # 保存したセッション情報とUser-Agentを適用してコンテキストを作成
        context = browser.new_context(
            storage_state=AUTH_STATE_PATH,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        
        try:
            # 外部メッセージが引数で渡されていない場合は、天気とニュースを取得してメッセージを組み立てる
            if not message:
                message = get_weather_and_news(page)
                
            print("🌐 ポスト作成ページに直接アクセス中...")
            # Xのポスト投稿インテント（意図）ページへダイレクトアクセス
            page.goto("https://x.com/intent/post")
            
            # もしログインが切れていてログイン画面にリダイレクトされた場合
            if "login" in page.url:
                print("⚠️ ログインセッションの期限が切れている可能性があります。")
                print("💡 一度 'auth_state.json' を削除して、再度ログインを行ってください。")
                browser.close()
                if os.path.exists(AUTH_STATE_PATH):
                    os.remove(AUTH_STATE_PATH)
                return

            print("🔍 投稿フォームの表示を確認中...")
            textarea_selector = 'div[data-testid="tweetTextarea_0"]'
            page.wait_for_selector(textarea_selector, timeout=15000)
            
            print("✍️ メッセージをタイピング中 (BAN防止のため人間らしくゆっくり入力)...")
            target_textarea = page.locator(textarea_selector).first
            target_textarea.click()
            target_textarea.press_sequentially(message, delay=120)
            
            time.sleep(2)
            
            print("🚀 ポストボタンをクリックします...")
            button_selector = '[data-testid="tweetButton"], [data-testid="tweetButtonInline"]'
            page.wait_for_selector(button_selector, timeout=10000)
            page.locator(button_selector).first.click()
            
            print("⏳ 投稿完了処理の完了を待機しています...")
            time.sleep(5)
            
            print("✅ Xへの自動投稿が正常に完了しました！")
            
        except Exception as e:
            print(f"❌ 自動投稿中にエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    run_bot(msg)
