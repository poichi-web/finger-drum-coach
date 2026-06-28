"""
Phase 0-3: パッド診断スクリプト（v3）

方針変更:
- 同じノート番号を送るパッドでも「全16パッドを記録」する
- チャタリング（200ms 以内の同一ノート連打）だけを除外
- 重複パッドは duplicate_of フィールドで注記

実行: .\\venv\\Scripts\\python.exe phase0/diagnose_pads.py
"""
import sys
import json
import time
import threading
import queue
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

try:
    import mido
except ImportError:
    print("[ERROR] mido がインストールされていません。")
    sys.exit(1)

PAD_COUNT = 16
CHATTER_SEC = 0.20   # 同一キーが200ms以内に来たらチャタリングとして無視
OUTPUT_PATH = Path(__file__).parent.parent / "pad_map.json"

DRUM_LABELS = [
    "Kick",    "Snare",    "Hi-Hat C", "Hi-Hat O",
    "Tom Hi",  "Tom Mid",  "Tom Lo",   "Crash",
    "Ride",    "Rim",      "Clap",     "Cowbell",
    "Perc 1",  "Perc 2",  "Perc 3",  "Perc 4",
]

def listen_port(port_name, event_queue, stop_event):
    try:
        with mido.open_input(port_name) as port:
            while not stop_event.is_set():
                for msg in port.iter_pending():
                    if msg.type == "note_on" and msg.velocity > 0:
                        event_queue.put({
                            "port": port_name,
                            "note": msg.note,
                            "channel": msg.channel + 1,
                            "velocity": msg.velocity,
                            "time": time.time(),
                        })
                time.sleep(0.005)
    except Exception as e:
        event_queue.put({"error": str(e), "port": port_name})

def main():
    all_ports = mido.get_input_names()
    if not all_ports:
        print("[ERROR] 入力 MIDI ポートが見つかりません。")
        sys.exit(1)

    target_ports = [p for p in all_ports
                    if any(k in p.upper() for k in ["SMC", "MVAVE", "M-VAVE", "POCKET"])] or all_ports

    print("=" * 60)
    print("  SMC-PAD パッド診断 v3（重複ノートも全記録）")
    print("=" * 60)
    print(f"監視ポート: {len(target_ports)} 件")
    for p in target_ports:
        print(f"  - {p}")
    print()
    print("16個のパッドを順番に叩いてください。")
    print("同じ音のパッドも「複製」として記録します（スキップしません）。")
    print("終了: 16パッド完了 または Ctrl+C")
    print()

    event_queue = queue.Queue()
    stop_event = threading.Event()
    for port_name in target_ports:
        t = threading.Thread(target=listen_port, args=(port_name, event_queue, stop_event), daemon=True)
        t.start()

    pad_records = []
    # チャタリングキーは (note, ch) のみ — 同一ノートが複数ポートに同時送信されるため port を含めない
    last_seen_time: dict[tuple, float] = {}
    # 重複検出も (note, ch) ベース
    registered_keys: dict[tuple, int] = {}

    pad_index = 0
    print(f"[{pad_index + 1:02d}/16] パッド 1 を叩いてください...", flush=True)

    try:
        while pad_index < PAD_COUNT:
            try:
                ev = event_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if "error" in ev:
                print(f"  [PORT ERROR] {ev['port']}: {ev['error']}")
                continue

            note = ev["note"]
            ch   = ev["channel"]
            port = ev["port"]
            vel  = ev["velocity"]
            now  = ev["time"]

            # チャタリングキー: port を除外（同一ノートが複数ポートに同時配信されるため）
            chatter_key = (note, ch)

            # チャタリング除外（200ms 以内の同一 note+ch）
            if now - last_seen_time.get(chatter_key, 0.0) < CHATTER_SEC:
                continue
            last_seen_time[chatter_key] = now

            # 重複チェック（スキップではなく注記のみ）
            dup_of = registered_keys.get(chatter_key)

            label = DRUM_LABELS[pad_index] if pad_index < len(DRUM_LABELS) else f"Pad{pad_index+1}"
            record = {
                "pad_index": pad_index,
                "label":     label,
                "note":      note,
                "channel":   ch,
                "port":      port,
                "sample_velocity": vel,
            }
            if dup_of is not None:
                record["duplicate_of_pad"] = dup_of
                dup_label = pad_records[dup_of]["label"]
                dup_flag  = f"  ⚠ Pad {dup_of+1}「{dup_label}」と同一ノート（Note={note}）"
            else:
                registered_keys[chatter_key] = pad_index
                dup_flag = ""

            pad_records.append(record)

            print(f"  ✓ Pad {pad_index+1:02d} | Note={note:3d} | Ch={ch} | Vel={vel:3d} | Port={port}", flush=True)
            if dup_flag:
                print(dup_flag, flush=True)

            pad_index += 1
            if pad_index < PAD_COUNT:
                print(f"\n[{pad_index + 1:02d}/16] パッド {pad_index+1} を叩いてください...", flush=True)

    except KeyboardInterrupt:
        print("\n[中断] Ctrl+C で停止しました。")

    stop_event.set()

    if not pad_records:
        print("[WARNING] 何も検出されませんでした。")
        return

    # 保存
    output = {
        "device":      "M-VAVE SMC-PAD POCKET",
        "ports_used":  target_ports,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pad_count":   len(pad_records),
        "pads":        {str(r["pad_index"]): r for r in pad_records},
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # サマリー表示
    print(f"\n{'=' * 60}")
    print(f"  記録完了: {len(pad_records)}/{PAD_COUNT} パッド → {OUTPUT_PATH.name}")
    print(f"{'=' * 60}")
    print(f"\n  {'Pad':>3}  {'Note':>4}  {'Ch':>3}  {'Label':<12}  備考")
    print("  " + "-" * 50)
    for r in pad_records:
        dup = f"  ← Pad {r['duplicate_of_pad']+1} と同一ノート" if "duplicate_of_pad" in r else ""
        print(f"  {r['pad_index']+1:>3}  {r['note']:>4}  {r['channel']:>3}  {r['label']:<12}{dup}")

    dup_count = sum(1 for r in pad_records if "duplicate_of_pad" in r)
    unique_count = len(pad_records) - dup_count
    print(f"\n  ユニークノート: {unique_count}  /  重複パッド: {dup_count}")
    if dup_count:
        print("  → 重複パッドは Phase 5 のリマップ機能で個別の音に割り当て直せます。")

    if len(pad_records) >= PAD_COUNT:
        print("\n[OK] 全16パッド記録完了！出力を Claude Code に貼り付けてください。")

if __name__ == "__main__":
    main()
