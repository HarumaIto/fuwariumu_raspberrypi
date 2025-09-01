from gpiozero import Button
import logging
import signal

# --- 設定項目 ---
SWITCH_PIN = 10

def setup_switch(callback_function):
    """
    スイッチの割り込みを設定する関数。

    Args:
        callback_function: スイッチが押されたときに呼び出す関数。
    """
    try:
        logging.info(f"GPIO {SWITCH_PIN} でスイッチの割り込みを設定します。")
        # スイッチはプルダウンされているため、立ち上がりエッジ(pressed)を検出
        switch = Button(SWITCH_PIN, bounce_time=0.1) # 0.1秒のバウンス時間を追加
        switch.when_pressed = callback_function
        logging.info("スイッチの準備が完了しました。")
        return switch # switchオブジェクトを返すように変更
    except Exception as e:
        logging.critical(f"スイッチの初期化中にエラーが発生しました: {e}", exc_info=True)
        return None

# --- デバッグ用のコード ---
def _handle_test_press():
    "テスト用にスイッチが押されたことを出力する関数"
    print("スイッチが押されました！")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("スイッチのデバッグモードです。")
    print(f"GPIO {SWITCH_PIN} に接続されたスイッチを押してください。")
    print("終了するには Ctrl+C を押してください。")

    switch_device = setup_switch(_handle_test_press)

    if switch_device:
        try:
            # プログラムが終了しないように待機
            signal.pause()
        except KeyboardInterrupt:
            print("\nプログラムを終了します。")
        finally:
            switch_device.close()
            print("GPIOリソースをクリーンアップしました。")
    else:
        print("スイッチのセットアップに失敗しました。")