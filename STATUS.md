# finger-drum-coach — STATUS

**状態**: 実装中（Phase 5 完了・Phase 4 未着手）
**最終更新**: 2026-06-28
**Notion仕様**: （後で貼る）

## 概要
M-VAVE SMC-PAD POCKET 専用コーチシステム。練習メニュー・メトロノーム・お手本再生・採点・リマップ機能を段階実装。

## 現状
- Phase 3 完了：FluidSynth + GeneralUser GS サウンドフォントによる発音。4×4 パッドグリッド表示・デモ再生・リアルタイム MIDI モニタリング稼働。
- Phase 5 完了：パッドリマップシステム実装済み。
  - `phase5/remap.py` — Remap クラス（ノート変換・JSON プリセット保存/読み込み）
  - `phase5/remap_editor.py` — テキスト UI エディタ（割当変更・プリセット管理）
  - `presets/standard.json` — 初期プリセット（底辺 4 パッドを Kick/Snare/ClosedHH/OpenHH に配置）
  - `phase3/demo_player.py` に `--remap PRESET` フラグ追加済み

## リマップ操作方法

```powershell
# エディタでパッド割当を編集・保存
.\venv\Scripts\python.exe phase5/remap_editor.py

# 組み込みプリセット "standard" を適用して起動
.\venv\Scripts\python.exe phase5/remap_editor.py --preset standard

# リマップを適用してデモプレイヤーを起動
.\venv\Scripts\python.exe phase3/demo_player.py --remap standard
```

## 残タスク
- [x] Phase 0-1: venv（Python 3.12）& mido/python-rtmidi インストール
- [x] Phase 0-2: MIDI ポート一覧確認（3ポート検出）
- [x] Phase 0-3: 16パッドマッピング確定 → pad_map.json 生成済み
- [x] Phase 1: メトロノーム（BPM/拍子可変・視覚カウント）
- [x] Phase 2: 練習プログラムエンジン（テーマ3種＋カスタム・BPM段階上げ）
- [x] Phase 3: お手本プレイ実演（FluidSynth + GeneralUser GS・4×4 グリッド表示）
- [ ] Phase 3 残: LED フィードバック実機検証（led_test.py）※後回し可
- [ ] Phase 4: 採点エンジン
- [x] Phase 5: パッド配置リマップ（完了）

## 次のアクション
Phase 4: 採点エンジン。
打鍵タイミング・ベロシティを記録し、お手本とのズレをスコア化。
「走る/もたる/特定パッドが弱い」フィードバック。
