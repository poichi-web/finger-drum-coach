"""
DrumSynth — pyfluidsynth + GM サウンドフォントによるドラム音源

DLL 配置: c:\\dev\\finger-drum-coach\\lib\\fluidsynth\\*.dll
SF2 配置: c:\\dev\\finger-drum-coach\\soundfonts\\GeneralUser.sf2
"""
import sys
import os
from pathlib import Path

# プロジェクト内の FluidSynth DLL を優先的に検索
_DLL_DIR = Path(__file__).parent.parent / "lib" / "fluidsynth"
if _DLL_DIR.exists():
    # PATH に追加（ctypes の DLL 探索に必要）
    os.environ["PATH"] = str(_DLL_DIR) + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(str(_DLL_DIR))
    except AttributeError:
        pass
    # libfluidsynth-3.dll を明示的にプリロード
    import ctypes
    for _dll in _DLL_DIR.glob("libfluidsynth*.dll"):
        try:
            ctypes.cdll.LoadLibrary(str(_dll))
            break
        except OSError:
            pass

SOUNDFONT_PATH = Path(__file__).parent.parent / "soundfonts" / "GeneralUser.sf2"

class DrumSynth:
    """FluidSynth ベースのリアルタイムドラム音源"""

    def __init__(self, sf_path: Path = SOUNDFONT_PATH):
        # 依存チェック
        try:
            import fluidsynth as _fs
            self._fs_mod = _fs
        except (ImportError, OSError) as e:
            print(f"[ERROR] pyfluidsynth の読み込みに失敗: {e}")
            print("  1. pip install pyfluidsynth")
            print("  2. lib/fluidsynth/ に FluidSynth DLL を配置")
            sys.exit(1)

        if not sf_path.exists():
            print(f"[ERROR] サウンドフォントが見つかりません: {sf_path}")
            print("  → soundfonts/ フォルダに GeneralUser.sf2 を置いてください。")
            sys.exit(1)

        self._synth = _fs.Synth(gain=0.7, samplerate=44100.0)

        # Windows audio ドライバを順番に試す
        for driver in ("wasapi", "dsound", "winmm"):
            try:
                self._synth.start(driver=driver)
                print(f"[FluidSynth] audio driver: {driver}")
                break
            except Exception as e:
                print(f"[FluidSynth] {driver} 失敗: {e}")
        else:
            print("[ERROR] FluidSynth のオーディオドライバをすべて試みましたが失敗しました。")
            print("  → ヘッドフォン/スピーカーを接続してから再起動してください。")
            sys.exit(1)

        sfid = self._synth.sfload(str(sf_path))
        if sfid == -1:
            print(f"[ERROR] サウンドフォントの読み込み失敗: {sf_path.name}")
            sys.exit(1)

        # チャンネル 9（0-indexed）= General MIDI ドラムパート
        self._synth.program_select(9, sfid, 128, 0)
        print(f"[FluidSynth] soundfont: {sf_path.name} ✓")

    def hit(self, note: int, velocity: int = 100):
        """パッドを叩く"""
        self._synth.noteon(9, note, max(1, min(127, velocity)))

    def release(self, note: int):
        """ノートオフ（通常は自動で OK）"""
        self._synth.noteoff(9, note)

    def close(self):
        self._synth.delete()
