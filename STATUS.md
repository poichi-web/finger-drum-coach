# finger-drum-coach — STATUS

**状態**: 実装中（Phase 1 完了・Phase 2 着手前）
**最終更新**: 2026-06-28
**Notion仕様**: （後で貼る）

## 概要
M-VAVE SMC-PAD POCKET 専用コーチシステム。練習メニュー・メトロノーム・お手本再生・採点・リマップ機能を段階実装。

## 現状
- Phase 0 開始：プロジェクト骨格作成 + 接続確認スクリプト整備
- venv 未作成（Phase 0 手順 2 待ち）

## 残タスク
- [x] Phase 0-1: venv（Python 3.12）& mido/python-rtmidi インストール
- [x] Phase 0-2: MIDI ポート一覧確認（3ポート検出）
- [x] Phase 0-3: 16パッドマッピング確定 → pad_map.json 生成済み
- [x] Phase 1: メトロノーム（BPM/拍子可変・視覚カウント・SDL=directsound）
- [ ] Phase 2: 練習プログラムエンジン
- [ ] Phase 3: お手本プレイ実演 & LED フィードバック検証
- [ ] Phase 4: 採点エンジン
- [ ] Phase 5: パッド配置リマップ

## 次のアクション
Phase 2: 練習プログラムエンジン実装。
レベル/テーマ指定 → ウォームアップ・課題・反復・クールダウンのメニュー自動生成。BPM 段階上げ対応。
