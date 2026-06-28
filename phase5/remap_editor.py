"""
Phase 5: パッドリマップエディタ（テキスト UI）

各パッドが送る MIDI ノートを、好みの GM ドラムノートに割り当て直します。
設定はプリセット JSON として presets/ フォルダに保存・切替可能です。

操作:
  [1-16]  : そのパッドの割当を変更
  [s]     : 現在の名前で保存
  [n]     : 別名で保存（新規プリセット）
  [L]     : プリセット一覧 → 切替
  [g]     : GM ドラムノート一覧を表示
  [q]     : 終了（未保存は破棄）

実行: .\\venv\\Scripts\\python.exe phase5/remap_editor.py
      .\\venv\\Scripts\\python.exe phase5/remap_editor.py --preset standard
"""
import sys
import json
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
from remap import Remap, GM_DRUMS, PRESETS_DIR

PAD_MAP_PATH = Path(__file__).parent.parent / "pad_map.json"


def note_name(n: int) -> str:
    return f"{n:3d}  {GM_DRUMS.get(n, '(カスタム)')}"


def load_pads() -> list[dict]:
    if not PAD_MAP_PATH.exists():
        print(f"[ERROR] {PAD_MAP_PATH} が見つかりません。Phase 0 でパッドマッピングを先に実行してください。")
        sys.exit(1)
    data = json.loads(PAD_MAP_PATH.read_text(encoding="utf-8"))
    return [data["pads"][str(i)] for i in range(16)]


def find_dup_notes(pads: list[dict]) -> set[int]:
    seen: set[int] = set()
    dups: set[int] = set()
    for p in pads:
        n = p["note"]
        if n in seen:
            dups.add(n)
        seen.add(n)
    return dups


def print_table(pads: list[dict], remap: Remap) -> None:
    dup_notes = find_dup_notes(pads)
    print()
    print(f"  プリセット: [{remap.name}]")
    print()
    print("  Pad │ 物理ノート (送信)                │ → 割当サウンド")
    print("  ────┼──────────────────────────────────┼──────────────────────────────")
    for i, p in enumerate(pads):
        pad_num = i + 1
        orig = p["note"]
        target = remap.apply(orig)
        dup_mark = "✱ " if orig in dup_notes else "  "
        orig_str = f"{orig:3d}  {GM_DRUMS.get(orig, '?'):<22}"
        tgt_str = f"{target:3d}  {GM_DRUMS.get(target, '?')}" if target != orig else "(変更なし)"
        print(f"  {pad_num:>3} │{dup_mark}{orig_str}│ → {tgt_str}")

    if dup_notes:
        notes_str = ", ".join(str(n) for n in sorted(dup_notes))
        print()
        print(f"  ✱ Note {notes_str} は複数パッドで共有 → 同じ割当になります")
    print()


def print_gm_list() -> None:
    print()
    print("  ── GM ドラムノート一覧 ──────────────")
    col = 0
    items = sorted(GM_DRUMS.items())
    for i, (note, name) in enumerate(items):
        print(f"  {note:3d}  {name:<22}", end="")
        col += 1
        if col == 2:
            print()
            col = 0
    if col:
        print()
    print()


def select_and_assign(pads: list[dict], remap: Remap, pad_num: int) -> None:
    idx = pad_num - 1
    orig = pads[idx]["note"]
    current = remap.apply(orig)
    print(f"\n  Pad {pad_num}: 物理ノート {orig} ({GM_DRUMS.get(orig, '?')})")
    print(f"  現在の割当: {note_name(current)}")
    print("  ノート番号を入力（35-81）、'r' でリセット、'g' でリスト表示、Enter でキャンセル:")
    raw = input("  > ").strip()

    if raw == "":
        print("  キャンセルしました。")
        return
    if raw == "g":
        print_gm_list()
        select_and_assign(pads, remap, pad_num)
        return
    if raw == "r":
        remap.clear(orig)
        print(f"  Pad {pad_num} をリセット → {note_name(orig)}")
        return
    try:
        target = int(raw)
        if not (0 <= target <= 127):
            raise ValueError
        remap.set(orig, target)
        print(f"  Pad {pad_num}: {orig} → {target} ({GM_DRUMS.get(target, 'カスタム')}) に設定しました。")
    except ValueError:
        print("  無効な入力です。0-127 の整数、'r'、'g'、または Enter を入力してください。")


def pick_preset() -> Remap | None:
    presets = Remap.list_presets()
    if not presets:
        print("  保存済みプリセットはありません。")
        return None
    print()
    for i, p in enumerate(presets):
        print(f"    [{i + 1}] {p.stem}")
    print("    [0] キャンセル")
    raw = input("  選択 > ").strip()
    try:
        idx = int(raw)
        if idx == 0:
            return None
        return Remap.from_file(presets[idx - 1])
    except (ValueError, IndexError):
        print("  無効な選択です。")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="パッドリマップエディタ")
    parser.add_argument("--preset", "-p", metavar="NAME", help="起動時に読み込むプリセット名")
    args = parser.parse_args()

    pads = load_pads()

    if args.preset:
        path = PRESETS_DIR / f"{args.preset}.json"
        if path.exists():
            remap = Remap.from_file(path)
            print(f"[Remap] '{remap.name}' を読み込みました。")
        else:
            print(f"[WARN] プリセット '{args.preset}' が見つかりません。新規で開始します。")
            remap = Remap(name=args.preset)
    else:
        presets = Remap.list_presets()
        if presets:
            print("\n  既存プリセットを読み込みますか？")
            loaded = pick_preset()
            remap = loaded if loaded else Remap(name="my_kit")
        else:
            remap = Remap(name="my_kit")

    print("\n================================================")
    print("  Finger Drum Coach — Remap Editor  (Phase 5)")
    print("================================================")

    while True:
        print_table(pads, remap)
        print("  [1-16] パッド選択  [s] 保存  [n] 別名保存  [L] プリセット切替  [g] GMリスト  [q] 終了")
        cmd = input("  > ").strip()

        if cmd.lower() == "q":
            print("  終了します。（未保存の変更は失われます）")
            break
        elif cmd.lower() == "s":
            path = remap.save()
            print(f"  保存しました: {path}")
        elif cmd.lower() == "n":
            name = input("  プリセット名 > ").strip()
            if name:
                path = remap.save(name)
                print(f"  保存しました: {path}")
        elif cmd == "L":
            loaded = pick_preset()
            if loaded:
                remap = loaded
                print(f"  '{remap.name}' を読み込みました。")
        elif cmd.lower() == "g":
            print_gm_list()
        elif cmd.isdigit() and 1 <= int(cmd) <= 16:
            select_and_assign(pads, remap, int(cmd))
        else:
            print("  無効なコマンドです。")


if __name__ == "__main__":
    main()
