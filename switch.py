from gpiozero import Button
import logging

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
        switch = Button(SWITCH_PIN)
        switch.when_pressed = callback_function
        logging.info("スイッチの準備が完了しました。")
        return True
    except Exception as e:
        logging.critical(f"スイッチの初期化中にエラーが発生しました: {e}", exc_info=True)
        return False
