"""
Phase 0-2: MIDI ポート一覧表示
実行: py -3.14 phase0/list_midi_ports.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

try:
    import mido
except ImportError:
    print("[ERROR] mido がインストールされていません。")
    print("  → py -3.14 -m pip install mido python-rtmidi")
    sys.exit(1)

print("=" * 50)
print("  MIDI ポート一覧")
print("=" * 50)

inputs = mido.get_input_names()
outputs = mido.get_output_names()

print(f"\n【入力ポート（{len(inputs)}件）】")
if inputs:
    for i, name in enumerate(inputs):
        marker = " ← SMC-PAD?" if "SMC" in name.upper() or "POCKET" in name.upper() or "MVAVE" in name.upper() or "M-VAVE" in name.upper() else ""
        print(f"  [{i}] {name}{marker}")
else:
    print("  （なし）")

print(f"\n【出力ポート（{len(outputs)}件）】")
if outputs:
    for i, name in enumerate(outputs):
        marker = " ← SMC-PAD?" if "SMC" in name.upper() or "POCKET" in name.upper() or "MVAVE" in name.upper() or "M-VAVE" in name.upper() else ""
        print(f"  [{i}] {name}{marker}")
else:
    print("  （なし）")

print()
if not inputs:
    print("[診断] 入力ポートが0件です。以下を確認してください：")
    print("  1. USB-C ケーブルで PC に接続済みか")
    print("  2. SMC-PAD の電源が入っているか")
    print("  3. デバイスマネージャーで「USB MIDIデバイス」または「USB Audio Device」が見えるか")
    print("     (Win+X → デバイスマネージャー → サウンド、ビデオ、およびゲームコントローラー)")
    print("  4. BLE接続の場合: 設定 → Bluetoothで「Bluetooth MIDI Device」が接続済みか")
else:
    print("[OK] ポートが検出されました。SMC-PAD のポート番号を控えて diagnose_pads.py を実行してください。")
