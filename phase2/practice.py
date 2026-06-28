"""
Phase 2: 練習プログラムエンジン（テキスト UI）

実行: .\\venv\\Scripts\\python.exe phase2/practice.py

テーマ選択 → ウォームアップ / 課題（BPM 段階上げ）/ クールダウン の順に進む。
各ステップでメトロノームを起動し、Enterで次へ進む。
"""
import sys
import os
import json
import subprocess
import time
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
sys.stdout.reconfigure(encoding="utf-8")

# ── pad_map 読み込み ────────────────────────────────────────
PAD_MAP_PATH = Path(__file__).parent.parent / "pad_map.json"

def load_pad_map() -> dict:
    if PAD_MAP_PATH.exists():
        data = json.loads(PAD_MAP_PATH.read_text(encoding="utf-8"))
        return data.get("pads", {})
    return {}

# ── 練習テーマ定義 ──────────────────────────────────────────
#
# 各テーマは steps リストを持つ。step の種類:
#   {"type": "info",  "msg": "..."}                     説明表示のみ
#   {"type": "metro", "label": "...", "bpm": N, "bars": N, "beats": N}
#       → メトロノームを N 小節分鳴らす（bars=0 で手動終了）
#
THEMES = {
    "1": {
        "name": "8ビート基礎",
        "desc": "4つ打ちキック + 2/4スネア + 8分HH の基本パターン",
        "level": "初級",
        "pad_roles": {
            "Kick": 36, "Snare": 38, "Hi-Hat C": 42,
        },
        "steps": [
            {"type": "info", "msg": (
                "【パターン】\n"
                "  HH :  x x x x x x x x  （8分音符、全拍）\n"
                "  Sn :  . . x . . . x .  （2拍目・4拍目）\n"
                "  Kk :  x . . . x . . .  （1拍目・3拍目）\n"
            )},
            {"type": "metro", "label": "ウォームアップ", "bpm": 60,  "bars": 4, "beats": 4},
            {"type": "metro", "label": "課題 Step 1",   "bpm": 70,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 2",   "bpm": 80,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 3",   "bpm": 90,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 4",   "bpm": 100, "bars": 8, "beats": 4},
            {"type": "metro", "label": "クールダウン",  "bpm": 70,  "bars": 4, "beats": 4},
            {"type": "info", "msg": "お疲れ様でした！ 次回は 100 BPM から始めましょう。"},
        ],
    },
    "2": {
        "name": "16分ハイハット",
        "desc": "ハイハットを16分音符で刻む",
        "level": "中級",
        "pad_roles": {
            "Hi-Hat C": 42, "Kick": 36, "Snare": 38,
        },
        "steps": [
            {"type": "info", "msg": (
                "【パターン】\n"
                "  HH : x x x x x x x x x x x x x x x x  （16分音符）\n"
                "  Sn :  . . . . x . . . . . . . x . . .  （2拍目・4拍目）\n"
                "  Kk :  x . . . . . . . x . . . . . . .  （1拍目・3拍目）\n"
            )},
            {"type": "metro", "label": "ウォームアップ", "bpm": 50,  "bars": 4, "beats": 4},
            {"type": "metro", "label": "課題 Step 1",   "bpm": 60,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 2",   "bpm": 70,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 3",   "bpm": 80,  "bars": 8, "beats": 4},
            {"type": "metro", "label": "クールダウン",  "bpm": 60,  "bars": 4, "beats": 4},
            {"type": "info", "msg": "お疲れ様でした！"},
        ],
    },
    "3": {
        "name": "フィルイン入門",
        "desc": "4小節に1回、簡単なフィルインを入れる",
        "level": "中級",
        "pad_roles": {
            "Tom Hi": 48, "Tom Mid": 45, "Tom Lo": 41,
            "Snare": 38,  "Kick": 36,
        },
        "steps": [
            {"type": "info", "msg": (
                "【フィルイン例（4拍目）】\n"
                "  Tom Hi → Tom Mid → Tom Lo → Snare\n"
                "  3拍目まで普通に8ビートを叩き、4拍目でフィルを入れる。\n"
            )},
            {"type": "metro", "label": "ウォームアップ（フィルなし）", "bpm": 60, "bars": 4, "beats": 4},
            {"type": "metro", "label": "課題 Step 1（フィルあり）",    "bpm": 60, "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 2",                  "bpm": 75, "bars": 8, "beats": 4},
            {"type": "metro", "label": "課題 Step 3",                  "bpm": 90, "bars": 8, "beats": 4},
            {"type": "metro", "label": "クールダウン",                  "bpm": 65, "bars": 4, "beats": 4},
            {"type": "info", "msg": "お疲れ様でした！"},
        ],
    },
    "4": {
        "name": "カスタム",
        "desc": "BPM・拍子・小節数を自分で設定して自由練習",
        "level": "自由",
        "pad_roles": {},
        "steps": [],  # run_custom() で動的生成
    },
}

# ── メトロノームを別プロセスで N 小節分だけ起動 ────────────
METRO_SCRIPT = Path(__file__).parent.parent / "phase1" / "metronome.py"
PYTHON       = Path(__file__).parent.parent / "venv" / "Scripts" / "python.exe"

def run_metro_step(step: dict):
    """メトロノーム画面を起動し、bars 小節後に自動終了。bars=0 なら手動終了。"""
    bpm   = step["bpm"]
    bars  = step.get("bars", 0)
    beats = step.get("beats", 4)

    secs = (60.0 / bpm) * beats * bars if bars > 0 else 0

    print(f"\n  ♩ = {bpm} BPM  |  {beats}/4  |  ", end="", flush=True)
    if bars > 0:
        print(f"{bars} 小節（約 {secs:.0f} 秒）")
    else:
        print("手動終了（ウィンドウを閉じるか Q）")
    print("  [Enter] でメトロノーム起動 / [s] でスキップ > ", end="", flush=True)

    choice = input().strip().lower()
    if choice == "s":
        print("  → スキップ")
        return

    # 環境変数を引き継いでメトロノームを起動
    env = os.environ.copy()
    proc = subprocess.Popen(
        [str(PYTHON), str(METRO_SCRIPT)],
        env=env,
    )

    if bars > 0:
        # 指定秒数待ってから終了
        deadline = time.time() + secs + 1.5  # 余裕 1.5 秒
        print(f"  （{secs:.0f} 秒後に自動で次へ進みます。早く進むには Enter）")
        # Enter か時間切れを待つ
        import threading
        entered = threading.Event()
        def wait_enter():
            input()
            entered.set()
        t = threading.Thread(target=wait_enter, daemon=True)
        t.start()
        while time.time() < deadline and not entered.is_set():
            time.sleep(0.1)
        proc.terminate()
    else:
        proc.wait()

# ── カスタム練習 ───────────────────────────────────────────
def run_custom():
    print("\n  ── カスタム練習 ──")
    try:
        bpm   = int(input("  BPM [60]: ").strip() or "60")
        beats = int(input("  拍子（拍数） [4]: ").strip() or "4")
        bars  = int(input("  小節数 [8]（0=手動終了）: ").strip() or "8")
    except ValueError:
        print("  [!] 数値を入力してください。")
        return
    run_metro_step({"bpm": bpm, "beats": beats, "bars": bars, "label": "カスタム"})

# ── テーマ実行 ─────────────────────────────────────────────
def run_theme(key: str):
    theme = THEMES[key]
    if key == "4":
        run_custom()
        return

    pad_map = load_pad_map()

    print(f"\n{'=' * 56}")
    print(f"  {theme['name']}  [{theme['level']}]")
    print(f"  {theme['desc']}")
    print(f"{'=' * 56}")

    # パッド対応表を表示
    if theme["pad_roles"] and pad_map:
        print("\n  【このテーマで使うパッド】")
        for role, gm_note in theme["pad_roles"].items():
            matched = [(i, p) for i, p in pad_map.items()
                       if p.get("note") == gm_note and "duplicate_of_pad" not in p]
            if matched:
                idx, p = matched[0]
                print(f"    Pad {int(idx)+1:>2}  Note={p['note']:>3}  → {role}")
            else:
                print(f"    Note={gm_note}  → {role}  （未マッピング）")

    total = len([s for s in theme["steps"] if s["type"] == "metro"])
    metro_idx = 0

    for step in theme["steps"]:
        if step["type"] == "info":
            print(f"\n{step['msg']}")
            input("  [Enter] で続ける > ")

        elif step["type"] == "metro":
            metro_idx += 1
            print(f"\n  ── ステップ {metro_idx}/{total}: {step['label']} ──")
            run_metro_step(step)

    print(f"\n{'=' * 56}")
    print(f"  練習完了！お疲れ様でした。")
    print(f"{'=' * 56}\n")

# ── メインメニュー ─────────────────────────────────────────
def main():
    print("\n" + "=" * 56)
    print("  Finger Drum Coach — 練習プログラム")
    print("=" * 56)

    while True:
        print("\n【テーマ選択】")
        for k, t in THEMES.items():
            print(f"  {k}) {t['name']:16}  [{t['level']}]  {t['desc']}")
        print("  q) 終了")
        print()
        choice = input("  番号を入力 > ").strip().lower()

        if choice == "q":
            print("終了します。")
            break
        elif choice in THEMES:
            run_theme(choice)
        else:
            print("  [!] 1〜4 または q を入力してください。")

if __name__ == "__main__":
    main()
