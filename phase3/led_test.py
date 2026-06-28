"""
Phase 3: SMC-PAD LED フィードバック テスト

SMC-PAD の出力ポートに Note On を送り、本体パッドの LED が光るか検証する。
光れば Phase 3 でリアルタイム LED 点灯を実装、光らなければ画面ビューアのみとする。

実行: .\\venv\\Scripts\\python.exe phase3/led_test.py
"""
import sys
import time
sys.stdout.reconfigure(encoding="utf-8")

try:
    import mido
except ImportError:
    print("[ERROR] mido がインストールされていません。")
    sys.exit(1)

PAD_KEYWORDS = ["smc", "mvave", "pocket"]
TEST_NOTES   = [36, 38, 42, 46, 48, 51]   # テストするノート番号
VELOCITY     = 100
ON_DUR       = 0.3   # 点灯時間（秒）
STEP_DUR     = 0.6   # ノート間隔（秒）

def main():
    outputs = mido.get_output_names()
    pad_outs = [p for p in outputs if any(k in p.lower() for k in PAD_KEYWORDS)]

    print("=" * 55)
    print("  SMC-PAD LED フィードバック テスト")
    print("=" * 55)

    if not pad_outs:
        print("[ERROR] SMC-PAD 出力ポートが見つかりません。")
        print("出力ポート一覧:")
        for p in outputs:
            print(f"  - {p}")
        sys.exit(1)

    print("\nSMC-PAD 出力ポート:")
    for p in pad_outs:
        print(f"  - {p}")
    print(f"\nNote {TEST_NOTES} に順番に Note On を送ります。")
    print("パッドの LED が光れば LED 制御が使えます。\n")
    input("[Enter] で開始 > ")

    with mido.open_output(pad_outs[0]) as out:
        for note in TEST_NOTES:
            print(f"  Note On  note={note} vel={VELOCITY} → ", end="", flush=True)
            out.send(mido.Message("note_on",  channel=9, note=note, velocity=VELOCITY))
            time.sleep(ON_DUR)
            out.send(mido.Message("note_off", channel=9, note=note, velocity=0))
            print("Note Off 送信済み")
            time.sleep(STEP_DUR - ON_DUR)

    print("\n全ノート送信完了。")
    print("パッドの LED が光った: → LED 制御あり（Phase 3 で実装可）")
    print("光らなかった          : → 画面ビューア方式を採用")
    result = input("\n結果を入力 [y=光った / n=光らなかった]: ").strip().lower()
    if result == "y":
        print("\n[OK] LED 制御が使えます！次回セッションで実装します。")
    else:
        print("\n[INFO] 画面ビューア（demo_player.py）を本線として進めます。")

if __name__ == "__main__":
    main()
