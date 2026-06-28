# finger-drum-coach — STATUS

**状態**: 実装中（Phase 3 完了・Phase 4 着手前）
**最終更新**: 2026-06-28
**Notion仕様**: （後で貼る）

## 概要
M-VAVE SMC-PAD POCKET 専用コーチシステム。練習メニュー・メトロノーム・お手本再生・採点・リマップ機能を段階実装。

## 現状
- Phase 3 完了：FluidSynth + GeneralUser GS サウンドフォントによる発音。4×4 パッドグリッド表示・デモ再生・リアルタイム MIDI モニタリング稼働。
- lib/fluidsynth/ に DLL、soundfonts/ に .sf2 配置済み（gitignore 対象）。

## 残タスク
- [x] Phase 0-1: venv（Python 3.12）& mido/python-rtmidi インストール
- [x] Phase 0-2: MIDI ポート一覧確認（3ポート検出）
- [x] Phase 0-3: 16パッドマッピング確定 → pad_map.json 生成済み
- [x] Phase 1: メトロノーム（BPM/拍子可変・視覚カウント）
- [x] Phase 2: 練習プログラムエンジン（テーマ3種＋カスタム・BPM段階上げ）
- [x] Phase 3: お手本プレイ実演（FluidSynth + GeneralUser GS・4×4 グリッド表示）
- [ ] Phase 3 残: LED フィードバック実機検証（led_test.py）※後回し可
- [ ] Phase 4: 採点エンジン
- [ ] Phase 5: パッド配置リマップ

## 次のアクション
Phase 4: 採点エンジン。
打鍵タイミング・ベロシティを記録し、お手本とのズレをスコア化。
「走る/もたる/特定パッドが弱い」フィードバック。
