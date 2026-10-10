#!/usr/bin/env python3
"""Sodalite Swap — neon match-3 arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/SODALITE_SWAP_ElbowOS.mp4")
TITLE, HANDLE = "SODALITE SWAP", "x.com/ElbowOS"
COLS, ROWS = 6, 9
CELL = 140
OX, OY = (W - COLS * CELL) // 2, 320
COLORS = [
    (0, 255, 255),   # cyan
    (255, 0, 255),   # magenta
    (255, 255, 0),   # yellow
    (0, 255, 128),   # lime
    (255, 128, 0),   # orange
]
BG = (8, 12, 32)
ACCENT = (180, 100, 255)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 72, bold=True)
        self.sfont = pygame.font.SysFont("Arial", 48, bold=True)
        self.grid = [[random.randint(0, 4) for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.sel = None
        self.particles = []
        self.auto_t = 0
        self.running = True

    def matches(self):
        to_clear = set()
        for r in range(ROWS):
            for c in range(COLS - 2):
                if self.grid[r][c] == self.grid[r][c+1] == self.grid[r][c+2] and self.grid[r][c] != -1:
                    to_clear.update([(r, c), (r, c+1), (r, c+2)])
        for c in range(COLS):
            for r in range(ROWS - 2):
                if self.grid[r][c] == self.grid[r+1][c] == self.grid[r+2][c] and self.grid[r][c] != -1:
                    to_clear.update([(r, c), (r+1, c), (r+2, c)])
        return to_clear

    def clear_matches(self):
        cleared = self.matches()
        if not cleared:
            return False
        for r, c in cleared:
            self.grid[r][c] = -1
            self.score += 10
            px, py = OX + c * CELL + CELL//2, OY + r * CELL + CELL//2
            for _ in range(8):
                self.particles.append([px, py, random.uniform(-4, 4), random.uniform(-6, -1), random.choice(COLORS), 20])
        return True

    def fall(self):
        for c in range(COLS):
            col = [self.grid[r][c] for r in range(ROWS) if self.grid[r][c] != -1]
            col = [-1] * (ROWS - len(col)) + col
            for r in range(ROWS):
                self.grid[r][c] = col[r]
        for c in range(COLS):
            for r in range(ROWS):
                if self.grid[r][c] == -1:
                    self.grid[r][c] = random.randint(0, 4)

    def swap(self, a, b):
        r1, c1 = a
        r2, c2 = b
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        if not self.matches():
            self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
            return False
        while self.clear_matches():
            self.fall()
        return True

    def autoplay(self):
        self.auto_t += 1
        if self.auto_t % 18 != 0:
            return
        for _ in range(40):
            r, c = random.randint(0, ROWS-1), random.randint(0, COLS-1)
            dirs = [(0,1), (1,0), (0,-1), (-1,0)]
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    if self.swap((r, c), (nr, nc)):
                        return

    def draw_gem(self, surf, x, y, col):
        if col < 0:
            return
        color = COLORS[col]
        rect = pygame.Rect(x + 12, y + 12, CELL - 24, CELL - 24)
        pygame.draw.rect(surf, color, rect, border_radius=24)
        glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, 80), glow.get_rect(), border_radius=30)
        surf.blit(glow, (x, y))
        pygame.draw.rect(surf, (255, 255, 255), rect, 4, border_radius=24)

    def draw(self):
        self.screen.fill(BG)
        # neon grid lines
        for i in range(COLS + 1):
            pygame.draw.line(self.screen, (40, 50, 90), (OX + i * CELL, OY), (OX + i * CELL, OY + ROWS * CELL), 2)
        for i in range(ROWS + 1):
            pygame.draw.line(self.screen, (40, 50, 90), (OX, OY + i * CELL), (OX + COLS * CELL, OY + i * CELL), 2)
        for r in range(ROWS):
            for c in range(COLS):
                self.draw_gem(self.screen, OX + c * CELL, OY + r * CELL, self.grid[r][c])
        # particles
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)
                continue
            pygame.draw.circle(self.screen, p[4], (int(p[0]), int(p[1])), 6)
        # overlays
        title = self.font.render(TITLE, True, ACCENT)
        self.screen.blit(title, (W//2 - title.get_width()//2, 80))
        sc = self.sfont.render(f"SCORE {self.score}", True, (0, 255, 200))
        self.screen.blit(sc, (W//2 - sc.get_width()//2, 180))
        handle = self.sfont.render(HANDLE, True, (255, 100, 200))
        self.screen.blit(handle, (W//2 - handle.get_width()//2, H - 120))
        pygame.display.flip()

    def run_play(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = e.pos
                    c = (mx - OX) // CELL
                    r = (my - OY) // CELL
                    if 0 <= r < ROWS and 0 <= c < COLS:
                        if self.sel is None:
                            self.sel = (r, c)
                        else:
                            sr, sc = self.sel
                            if abs(sr - r) + abs(sc - c) == 1:
                                self.swap(self.sel, (r, c))
                            self.sel = None
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def run_record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-movflags", "+faststart", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(frames):
            self.autoplay()
            self.draw()
            raw = pygame.image.tostring(self.screen, "RGB")
            proc.stdin.write(raw)
        proc.stdin.close()
        proc.wait()
        pygame.quit()

if __name__ == "__main__":
    g = Game()
    if RECORD:
        g.run_record()
    else:
        g.run_play()
