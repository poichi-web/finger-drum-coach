"""
Phase 3: デモプレイヤー + リアルタイム MIDI モニター

- パッドを叩くと FluidSynth + GM サウンドフォントで即発音
- デモパターンを再生しながら 4×4 パッドグリッドで点灯表示
- pygame は表示専用（mixer 不使用）

操作:
  Space       : デモ 開始 / 停止
  ↑ / ↓       : BPM ±1
  Shift+↑/↓   : BPM ±5
  1 / 2 / 3   : パターン切替
  Q / Esc     : 終了

実行: .\\venv\\Scripts\\python.exe phase3/demo_player.py
"""
import sys
import os
import json
import time
import threading
import queue
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

try:
    import pygame
    import mido
except ImportError as e:
    print(f"[ERROR] {e}\n  → pip install pygame mido python-rtmidi")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from sounds import DrumSynth

# ── 定数 ────────────────────────────────────────────────────
WIN_W, WIN_H = 720, 500
BPM_MIN, BPM_MAX = 30, 240

BG         = (15, 17, 28)
PAD_OFF    = (35, 38, 58)
PAD_DEMO   = (255, 190, 30)
PAD_USER   = (60, 210, 120)
PAD_BORDER = (55, 60, 90)
TEXT_W     = (210, 215, 235)
TEXT_G     = (90, 95, 125)
ACCENT     = (255, 190, 30)
GREEN      = (70, 220, 110)

PAD_KEYWORDS = ["smc", "mvave", "pocket"]

# ── デモパターン ─────────────────────────────────────────────
PATTERNS = {
    "1": {
        "name": "8ビート",
        "desc": "Kick(1/3) + Snare(2/4) + HH 8分",
        "bpm": 80,
        "steps": 16,
        "tracks": {
            36: [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
            38: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
            42: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        },
    },
    "2": {
        "name": "16分 HH",
        "desc": "HH を全16分で刻む",
        "bpm": 75,
        "steps": 16,
        "tracks": {
            36: [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
            38: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
            42: [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],
        },
    },
    "3": {
        "name": "フィルイン",
        "desc": "3小節8ビート → 1小節フィル",
        "bpm": 75,
        "steps": 64,
        "tracks": {
            36: ([1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0] * 3 + [0]*16),
            38: ([0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0] * 3
                 + [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0]),
            42: ([1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0] * 3 + [0]*16),
            48: [0]*48 + [1,1,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
            45: [0]*48 + [0,0,1,1, 0,0,0,0, 0,0,0,0, 0,0,0,0],
            41: [0]*48 + [0,0,0,0, 1,1,0,0, 0,0,0,0, 0,0,0,0],
        },
    },
}

# ── pad_map 読み込み ────────────────────────────────────────
PAD_MAP_PATH = Path(__file__).parent.parent / "pad_map.json"

def load_note_to_pad() -> dict:
    if not PAD_MAP_PATH.exists():
        return {}
    data = json.loads(PAD_MAP_PATH.read_text(encoding="utf-8"))
    result = {}
    for idx_str, info in data.get("pads", {}).items():
        note = info["note"]
        if note not in result:
            result[note] = int(idx_str)
    return result

# ── シーケンサースレッド ─────────────────────────────────────
class Sequencer(threading.Thread):
    def __init__(self, q: queue.Queue):
        super().__init__(daemon=True)
        self.q = q
        self.bpm = 80
        self.steps = 16
        self.playing = False
        self._stop = threading.Event()
        self._reset = threading.Event()
        self._lock = threading.Lock()

    def run(self):
        while not self._stop.is_set():
            if not self.playing:
                time.sleep(0.01)
                continue
            self._reset.clear()
            with self._lock:
                interval = (60.0 / self.bpm) / 4
                steps = self.steps
            step = 0
            next_t = time.perf_counter()
            while self.playing and not self._stop.is_set() and not self._reset.is_set():
                self.q.put(("step", step % steps))
                step += 1
                next_t += interval
                while time.perf_counter() < next_t:
                    if self._reset.is_set() or not self.playing:
                        break
                    time.sleep(0.001)

    def set_bpm(self, v):
        with self._lock:
            self.bpm = max(BPM_MIN, min(BPM_MAX, v))
        if self.playing:
            self._reset.set()

    def set_steps(self, v):
        with self._lock:
            self.steps = v
        if self.playing:
            self._reset.set()

    def toggle(self):
        self.playing = not self.playing
        if self.playing:
            self._reset.set()

    def stop(self):
        self._stop.set()

# ── MIDI 入力スレッド ────────────────────────────────────────
def midi_listener(q: queue.Queue, stop: threading.Event):
    ports = [p for p in mido.get_input_names()
             if any(k in p.lower() for k in PAD_KEYWORDS)]
    if not ports:
        print("[WARN] SMC-PAD 入力ポートが見つかりません。")
        return

    def _listen(port_name):
        try:
            with mido.open_input(port_name) as port:
                for msg in port:
                    if stop.is_set():
                        break
                    if msg.type == "note_on" and msg.velocity > 0:
                        q.put(("midi", msg.note, msg.velocity))
        except Exception as e:
            print(f"[MIDI] {port_name}: {e}")

    for p in ports:
        threading.Thread(target=_listen, args=(p,), daemon=True).start()

# ── パッドグリッド描画 ────────────────────────────────────────
def draw_pad_grid(screen, font, pad_flash, pad_user_flash, now):
    CELL, MARGIN = 80, 14
    grid_w = 4 * CELL + 3 * MARGIN
    grid_h = 4 * CELL + 3 * MARGIN
    ox = (WIN_W - grid_w) // 2
    oy = WIN_H - grid_h - 40

    for pad_idx in range(16):
        row = 3 - (pad_idx // 4)
        col = pad_idx % 4
        x = ox + col * (CELL + MARGIN)
        y = oy + row * (CELL + MARGIN)

        demo_lit = now < pad_flash.get(pad_idx, 0)
        user_lit = now < pad_user_flash.get(pad_idx, 0)

        if demo_lit and user_lit:
            color = (200, 240, 100)
        elif user_lit:
            color = PAD_USER
        elif demo_lit:
            color = PAD_DEMO
        else:
            color = PAD_OFF

        pygame.draw.rect(screen, color, (x, y, CELL, CELL), border_radius=10)
        pygame.draw.rect(screen, PAD_BORDER, (x, y, CELL, CELL), 2, border_radius=10)

        num = font.render(str(pad_idx + 1), True,
                          BG if (demo_lit or user_lit) else TEXT_G)
        screen.blit(num, (x + CELL//2 - num.get_width()//2,
                          y + CELL//2 - num.get_height()//2))

# ── メイン ────────────────────────────────────────────────────
def main():
    # FluidSynth 音源を初期化（表示より先）
    synth = DrumSynth()

    # pygame は表示専用（mixer 不要）
    os.environ["SDL_VIDEODRIVER"] = os.environ.get("SDL_VIDEODRIVER", "")
    pygame.display.init()
    pygame.font.init()

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Finger Drum Coach — Demo Player")
    clock = pygame.time.Clock()

    font_lg  = pygame.font.SysFont("arialblack,arial", 52, bold=True)
    font_md  = pygame.font.SysFont("meiryo,arial", 28)
    font_sm  = pygame.font.SysFont("meiryo,arial", 18)
    font_pad = pygame.font.SysFont("arialblack,arial", 20, bold=True)

    note_to_pad = load_note_to_pad()

    seq_q = queue.Queue()
    midi_q = queue.Queue()
    seq = Sequencer(seq_q)
    seq.start()

    midi_stop = threading.Event()
    threading.Thread(target=midi_listener, args=(midi_q, midi_stop), daemon=True).start()

    pat_key = "1"
    pattern = PATTERNS[pat_key]
    bpm = pattern["bpm"]
    seq.bpm = bpm
    seq.steps = pattern["steps"]

    pad_flash: dict = {}
    pad_user_flash: dict = {}
    FLASH_DUR = 0.13

    running = True
    while running:
        now = time.perf_counter()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                step = 5 if (mods & pygame.KMOD_SHIFT) else 1

                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_SPACE:
                    seq.toggle()
                    if not seq.playing:
                        pad_flash.clear()
                elif ev.key == pygame.K_UP:
                    bpm = min(BPM_MAX, bpm + step)
                    seq.set_bpm(bpm); bpm = seq.bpm
                elif ev.key == pygame.K_DOWN:
                    bpm = max(BPM_MIN, bpm - step)
                    seq.set_bpm(bpm); bpm = seq.bpm
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    pat_key = str(ev.key - pygame.K_0)
                    pattern = PATTERNS[pat_key]
                    bpm = pattern["bpm"]
                    seq.set_bpm(bpm); seq.set_steps(pattern["steps"])
                    bpm = seq.bpm; pad_flash.clear()

        # シーケンサー tick
        try:
            while True:
                _, step = seq_q.get_nowait()
                for note, seq_steps in pattern["tracks"].items():
                    if step < len(seq_steps) and seq_steps[step]:
                        synth.hit(note, 90)
                        pad_idx = note_to_pad.get(note)
                        if pad_idx is not None:
                            pad_flash[pad_idx] = now + FLASH_DUR
        except queue.Empty:
            pass

        # MIDI 入力
        try:
            while True:
                _, note, vel = midi_q.get_nowait()
                synth.hit(note, vel)
                pad_idx = note_to_pad.get(note)
                if pad_idx is not None:
                    pad_user_flash[pad_idx] = now + FLASH_DUR
        except queue.Empty:
            pass

        # 描画
        screen.fill(BG)

        p_name = font_lg.render(pattern["name"], True, ACCENT)
        screen.blit(p_name, (WIN_W//2 - p_name.get_width()//2, 18))
        p_desc = font_sm.render(pattern["desc"], True, TEXT_G)
        screen.blit(p_desc, (WIN_W//2 - p_desc.get_width()//2, 76))

        bpm_surf = font_md.render(f"♩ = {bpm}", True, TEXT_W)
        screen.blit(bpm_surf, (WIN_W//2 - bpm_surf.get_width()//2, 110))

        st = "▶  DEMO 再生中" if seq.playing else "■  停止  （パッドを叩いて発音確認可）"
        sc = GREEN if seq.playing else (140, 140, 170)
        st_surf = font_sm.render(st, True, sc)
        screen.blit(st_surf, (WIN_W//2 - st_surf.get_width()//2, 148))

        draw_pad_grid(screen, font_pad, pad_flash, pad_user_flash, now)

        hints = ["Space: デモ開始/停止", "1/2/3: パターン切替",
                 "↑↓ (Shift:±5): BPM",  "Q: 終了"]
        for i, h in enumerate(hints):
            t = font_sm.render(h, True, TEXT_G)
            screen.blit(t, (30 + (i % 2) * (WIN_W//2), WIN_H - 56 + (i//2) * 22))

        pygame.display.flip()
        clock.tick(60)

    seq.stop()
    midi_stop.set()
    synth.close()
    pygame.quit()

if __name__ == "__main__":
    main()
