"""
Phase 1: メトロノーム

操作:
  Space         : 開始 / 停止
  ↑ / ↓         : BPM +1 / -1
  Shift + ↑/↓   : BPM +5 / -5
  2〜9           : 拍子（拍数/小節）変更
  Q / Escape    : 終了
"""
import sys
import math
import array
import time
import threading
import queue

import os
os.environ.setdefault("SDL_AUDIODRIVER", "directsound")

sys.stdout.reconfigure(encoding="utf-8")

try:
    import pygame
except ImportError:
    print("[ERROR] pygame がインストールされていません。")
    print("  → pip install pygame")
    sys.exit(1)

# ── 定数 ──────────────────────────────────────────────────
SAMPLE_RATE  = 44100
WIN_W, WIN_H = 680, 380

BG        = (18,  20,  32)
ACCENT_ON = (255, 190,  30)   # 1拍目 点灯
BEAT_ON   = (60,  160, 255)   # 2拍目以降 点灯
DOT_OFF   = (45,  48,  68)    # 消灯
TEXT_W    = (210, 215, 230)
TEXT_G    = (100, 105, 130)
GREEN     = (80,  230, 120)
RED       = (210,  70,  70)

BPM_MIN, BPM_MAX = 30, 300

# ── サウンド生成（ステレオ 16-bit）──────────────────────
def _gen_click(freq: float, volume: float = 0.85, ms: int = 60) -> array.array:
    """signed 16-bit stereo PCM (L/R 交互) — numpy 不要"""
    n = int(SAMPLE_RATE * ms / 1000)
    buf = array.array("h")
    for i in range(n):
        t   = i / SAMPLE_RATE
        env = math.exp(-t * 38)
        v   = int(volume * 32767 * math.sin(2 * math.pi * freq * t) * env)
        v   = max(-32767, min(32767, v))
        buf.append(v)  # L
        buf.append(v)  # R
    return buf

# ── タイマースレッド ───────────────────────────────────
class Ticker(threading.Thread):
    def __init__(self, q: queue.Queue):
        super().__init__(daemon=True)
        self.q       = q
        self.bpm     = 120
        self.beats   = 4
        self.playing = False
        self._stop   = threading.Event()
        self._reset  = threading.Event()
        self._lock   = threading.Lock()

    def run(self):
        while not self._stop.is_set():
            if not self.playing:
                time.sleep(0.01)
                continue

            self._reset.clear()
            with self._lock:
                interval = 60.0 / self.bpm
                beats    = self.beats

            beat   = 0
            next_t = time.perf_counter()

            while self.playing and not self._stop.is_set() and not self._reset.is_set():
                self.q.put(("tick", beat % beats))
                beat   += 1
                next_t += interval
                # 細かくポーリングしてリセット信号に即応
                while time.perf_counter() < next_t:
                    if self._reset.is_set() or not self.playing:
                        break
                    time.sleep(0.001)

    def set_bpm(self, v: int):
        with self._lock:
            self.bpm = max(BPM_MIN, min(BPM_MAX, v))
        if self.playing:
            self._reset.set()

    def set_beats(self, v: int):
        with self._lock:
            self.beats = v
        if self.playing:
            self._reset.set()

    def toggle(self):
        self.playing = not self.playing
        if self.playing:
            self._reset.set()

    def stop(self):
        self._stop.set()

# ── メイン ────────────────────────────────────────────
def main():
    pygame.init()
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
    except pygame.error:
        pygame.mixer.init()

    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Finger Drum Coach — Metronome")
    clock  = pygame.time.Clock()

    # クリック音: アクセント（高音）/ 通常（低音）
    snd_hi = pygame.mixer.Sound(buffer=_gen_click(1050, 0.9, 55))
    snd_lo = pygame.mixer.Sound(buffer=_gen_click( 620, 0.6, 50))

    # フォント（日本語が無ければ ASCII のみ表示）
    font_bpm  = pygame.font.SysFont("arialblack,arial",       88, bold=True)
    font_note = pygame.font.SysFont("segoeuisymbol,arial",    42)
    font_sig  = pygame.font.SysFont("arialblack,arial",       38, bold=True)
    font_sm   = pygame.font.SysFont("meiryo,arial",           19)

    tick_q  = queue.Queue()
    ticker  = Ticker(tick_q)
    ticker.start()

    bpm          = 120
    beats        = 4
    current_beat = -1
    flash_until  = 0.0

    running = True
    while running:
        now = time.perf_counter()

        # ── イベント ──────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                step = 5 if (mods & pygame.KMOD_SHIFT) else 1

                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif ev.key == pygame.K_SPACE:
                    ticker.toggle()
                    if not ticker.playing:
                        current_beat = -1

                elif ev.key == pygame.K_UP:
                    bpm = min(BPM_MAX, bpm + step)
                    ticker.set_bpm(bpm)
                    bpm = ticker.bpm

                elif ev.key == pygame.K_DOWN:
                    bpm = max(BPM_MIN, bpm - step)
                    ticker.set_bpm(bpm)
                    bpm = ticker.bpm

                elif pygame.K_2 <= ev.key <= pygame.K_9:
                    beats = ev.key - pygame.K_0
                    ticker.set_beats(beats)
                    current_beat = -1

        # ── tick 受信 ──────────────────────────────────
        try:
            while True:
                _, beat = tick_q.get_nowait()
                current_beat = beat
                flash_until  = now + 0.12
                (snd_hi if beat == 0 else snd_lo).play()
        except queue.Empty:
            pass

        # ── 描画 ───────────────────────────────────────
        screen.fill(BG)

        # ---- BPM 表示（中央やや上）----
        bpm_surf  = font_bpm.render(str(bpm), True, ACCENT_ON)
        note_surf = font_note.render("= ", True, TEXT_G)
        # ♩記号（フォントにあれば）
        q_surf    = font_note.render("♩", True, TEXT_G)

        bpm_x = WIN_W // 2 - bpm_surf.get_width() // 2
        bpm_y = WIN_H // 2 - 105

        q_x = bpm_x - note_surf.get_width() - q_surf.get_width() - 4
        screen.blit(q_surf,  (q_x, bpm_y + 16))
        screen.blit(note_surf,(q_x + q_surf.get_width(), bpm_y + 16))
        screen.blit(bpm_surf, (bpm_x, bpm_y))

        # ---- 拍子ドット ----
        r   = 20
        gap = r * 3
        total_w = beats * gap - (gap - r * 2)
        x0  = (WIN_W - total_w) // 2 + r
        y0  = WIN_H // 2 + 60

        for i in range(beats):
            cx = x0 + i * gap
            lit = (i == current_beat and now < flash_until)
            if lit:
                color = ACCENT_ON if i == 0 else BEAT_ON
                pygame.draw.circle(screen, color, (cx, y0), r)
                # 光彩
                pygame.draw.circle(screen, color, (cx, y0), r + 4, 2)
            else:
                pygame.draw.circle(screen, DOT_OFF, (cx, y0), r)
                if i == 0:
                    # 1拍目は枠を明るくして区別
                    pygame.draw.circle(screen, (100, 90, 40), (cx, y0), r, 3)

        # ---- 拍子（右上）----
        sig_surf = font_sig.render(f"{beats}/4", True, TEXT_G)
        screen.blit(sig_surf, (WIN_W - sig_surf.get_width() - 18, 14))

        # ---- ステータス（左上）----
        if ticker.playing:
            st_text, st_col = "▶  PLAYING", GREEN
        else:
            st_text, st_col = "■  STOPPED", RED
        st_surf = font_sm.render(st_text, True, st_col)
        screen.blit(st_surf, (18, 18))

        # ---- キーヒント（下段）----
        hints = [
            "Space : 開始 / 停止",
            "↑↓ : BPM ±1    Shift+↑↓ : ±5",
            "2〜9 : 拍子変更",
            "Q / Esc : 終了",
        ]
        col_w = WIN_W // 2
        for i, h in enumerate(hints):
            col = i // 2
            row = i  % 2
            t = font_sm.render(h, True, TEXT_G)
            screen.blit(t, (18 + col * col_w, WIN_H - 54 + row * 24))

        pygame.display.flip()
        clock.tick(60)

    ticker.stop()
    pygame.quit()

if __name__ == "__main__":
    main()
