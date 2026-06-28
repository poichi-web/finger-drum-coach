# finger-drum-coach

M-VAVE SMC-PAD POCKET 専用フィンガードラム練習コーチ。

## フェーズ構成

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | 環境構築・接続確認・パッドマッピング | 🚧 進行中 |
| 1 | メトロノーム | 未着手 |
| 2 | 練習プログラムエンジン | 未着手 |
| 3 | お手本プレイ実演 + LED 検証 | 未着手 |
| 4 | 採点エンジン | 未着手 |
| 5 | パッド配置リマップ | 未着手 |

---

## Phase 0: 環境セットアップ手順

### 手順 1: Python 仮想環境を作成してパッケージをインストール

```powershell
cd c:\dev\finger-drum-coach
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> **注意**: `python-rtmidi` は Python 3.12 の wheel が必要です。Python 3.14 ではビルドが失敗します。
>
> **pip が失敗する場合（SSL エラー）**
> ```powershell
> pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
> ```

### 手順 2: SMC-PAD を USB-C で PC に接続

1. USB-C ケーブルで PC に差す（BLE は後回し）
2. SMC-PAD の電源を入れる
3. デバイスマネージャーで認識を確認
   - Win+X → デバイスマネージャー
   - 「サウンド、ビデオ、およびゲームコントローラー」に USB MIDI 系デバイスが出ればOK

### 手順 3: MIDI ポート一覧を確認

```powershell
py -3.14 phase0/list_midi_ports.py
```

出力例（SMC-PAD が見えている場合）:
```
【入力ポート（2件）】
  [0] Microsoft GS Wavetable Synth
  [1] SMC-PAD POCKET  ← SMC-PAD?
```

> **ポートに SMC-PAD が出ない場合**
> → README 末尾の「接続トラブルシューティング」を参照。

### 手順 4: 16パッドのマッピングを確定

```powershell
py -3.14 phase0/diagnose_pads.py 1   # 1 は SMC-PAD のポート番号
```

画面の指示に従って16パッドを順番に叩くと `pad_map.json` が生成されます。
内容を Claude Code に貼り付けて確認を取ってから Phase 1 へ。

---

## 接続トラブルシューティング

### USB-C で認識されない

| チェック項目 | 対処 |
|---|---|
| ドライバ未インストール | デバイスマネージャーに「不明なデバイス」があれば右クリック→ドライバ更新 |
| ケーブルが充電専用 | データ転送対応の USB-C ケーブルに交換 |
| Windows MIDI ドライバ不足 | [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) をインストールして仮想ポートを作成 |

### BLE しか使えない場合

1. Windows の Bluetooth 設定で SMC-PAD をペアリング
2. [MIDIberry](https://apps.microsoft.com/detail/9n39720h2m05) (無料、Microsoft Store) をインストールして BLE→ローカル MIDI ブリッジを作成
3. `list_midi_ports.py` で「Bluetooth MIDI」ポートが出ればOK

---

## ファイル構成

```
finger-drum-coach/
├── README.md
├── STATUS.md
├── requirements.txt
├── pad_map.json          # Phase 0-3 で生成（gitignore 対象外）
├── phase0/
│   ├── list_midi_ports.py    # MIDI ポート一覧
│   └── diagnose_pads.py      # パッドマッピング診断
├── phase1/               # メトロノーム（未着手）
├── phase2/               # 練習エンジン（未着手）
├── phase3/               # お手本再生（未着手）
├── phase4/               # 採点（未着手）
├── phase5/               # リマップ（未着手）
└── logs/                 # 練習ログ CSV/JSON（gitignore）
```
