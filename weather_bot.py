import os
import time
from playwright.sync_api import sync_playwright

# 基準パスの取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_PATH = os.path.join(BASE_DIR, "weather.png")

# 京都府南部の天気予報URL
URL = "https://weather.yahoo.co.jp/weather/jp/26/6110.html"

def run():
    print("🤖 Playwrightを起動しています...")
    with sync_playwright() as p:
        # Chromiumブラウザを起動 (headless=Trueで裏で高速実行)
        # ※目で動作を見たい場合は headless=False に変更できます。
        browser = p.chromium.launch(headless=True)
        
        # 新しいブラウザコンテキストとページを開く
        page = browser.new_page()
        
        # 画面サイズ（ビューポート）を設定
        page.set_viewport_size({"width": 1280, "height": 800})
        
        print(f"🌐 天気予報ページにアクセス中: {URL}")
        page.goto(URL, wait_until="networkidle") # ネットワーク読み込みが完了するまで待つ
        
        print("🔍 天気情報のテキストを抽出中...")
        try:
            # 天気予報テーブルの「今日」のtd要素（1番目のtd）を取得
            today_element = page.locator("#main .forecastCity > table > tbody > tr > td").first
            
            # テキストの取得
            weather = today_element.locator("p.pict").inner_text().strip()
            high_temp = today_element.locator("li.high em").inner_text().strip()
            low_temp = today_element.locator("li.low em").inner_text().strip()
            
            print("\n==============================")
            print("🌤️ 今日の京都府南部の天気概況")
            print("==============================")
            print(f"今日の天気: {weather}")
            print(f"最高気温  : {high_temp}℃")
            print(f"最低気温  : {low_temp}℃")
            print("==============================\n")
            
        except Exception as e:
            print(f"⚠️ テキスト情報の取得に失敗しました: {e}")
            
        print("📸 天気予報エリアのスクリーンショットを撮影中...")
        try:
            # 今日・明日を含む天気予報エリア全体（.forecastCity）を指定
            forecast_box_selector = "#main .forecastCity"
            page.wait_for_selector(forecast_box_selector, timeout=5000)
            
            # 対象の要素を取得
            element = page.locator(forecast_box_selector)
            
            # 要素部分だけのスクリーンショットを撮影して保存
            element.screenshot(path=SCREENSHOT_PATH)
            print(f"✅ スクリーンショットを保存しました: {SCREENSHOT_PATH}")
            
        except Exception as e:
            print(f"⚠️ スクリーンショットの撮影に失敗しました: {e}")
            
        # ブラウザを閉じる
        browser.close()
        print("🤖 ブラウザを終了しました。")

if __name__ == "__main__":
    run()
