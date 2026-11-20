#!/usr/bin/env python3
"""news-image-20261120: draw one image summing up the world news of
Friday 20 November 2026 and write it to /output/entry.png.

Pure Python standard library: no network, no files read, no Pillow.
The picture is drawn with a small built-in 5x7 bitmap font (glyphs
stored as seven 5-bit rows) and encoded as a PNG with zlib, so the
program is deterministic: two runs write the same bytes. Run it as
the grader does:
    MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ------------------------------------------------------------
PAPER = (247, 242, 231)
INK = (20, 20, 20)
NAVY = (14, 42, 71)
RED = (180, 35, 24)
GOLD = (201, 162, 39)
GREY = (90, 90, 90)
CARD = (255, 255, 255)
LINE = (216, 210, 196)
SKY = (70, 130, 180)
GREEN = (46, 125, 50)
ORANGE = (214, 110, 30)

# --- 5x7 bitmap font ----------------------------------------------------
# Each glyph is 7 rows; each row is a 5-bit value, bit 4 = left pixel.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x02, 0x04),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x02, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
}

# Dashes, curly quotes and bullets map to plain glyphs.
ALIASES = {"\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
           "\u2022": "*", "\u00b7": "*", "\u201c": '"', "\u201d": '"'}


def glyph(ch):
    return FONT.get(ALIASES.get(ch, ch), FONT["?"])


def text_width(text, scale):
    """Width in pixels of text drawn at the given scale (6 px per char)."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    """An RGB pixel buffer with tiny drawing helpers."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def _put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill(self, x, y, w, h, color):
        x0, x1 = max(0, x), min(self.w, x + w)
        if x1 <= x0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + x0) * 3
            self.px[base:base + len(row)] = row

    def hrule(self, x, y, w, color, t=1):
        self.fill(x, y, w, t, color)

    def vrule(self, x, y, h, color, t=1):
        self.fill(x, y, t, h, color)

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            if abs(dy) > r:
                continue
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill(cx - dx, yy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, t=2):
        for k in range(t):
            rr = r - k
            for yy in range(cy - rr, cy + rr + 1):
                dy = yy - cy
                if abs(dy) > rr:
                    continue
                dx = int((rr * rr - dy * dy) ** 0.5)
                self._put(cx - dx, yy, color)
                self._put(cx + dx, yy, color)

    def segment(self, x0, y0, x1, y1, color):
        """Bresenham line segment."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def burst(self, cx, cy, r, color):
        """Starburst: 8 spikes from a centre disc (explosion flash)."""
        vecs = [(1, 0), (0.7071, 0.7071), (0, 1), (-0.7071, 0.7071),
                (-1, 0), (-0.7071, -0.7071), (0, -1), (0.7071, -0.7071)]
        self.disc(cx, cy, r // 3, color)
        for vx, vy in vecs:
            x1 = cx + int(r * vx)
            y1 = cy + int(r * vy)
            self.segment(cx, cy, x1, y1, color)
            self.disc(x1, y1, 2, color)

    def glyph_at(self, x, y, ch, scale, color):
        rows = glyph(ch)
        for r in range(7):
            bits = rows[r]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    self.fill(x + col * scale, y + r * scale,
                              scale, scale, color)

    def text(self, x, y, s, scale, color):
        for ch in s:
            self.glyph_at(x, y, ch, scale, color)
            x += 6 * scale
        return x

    def text_mid(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def para(self, x, y, s, scale, color, max_width, leading=None):
        """Wrapped text block; returns the y just below the last line."""
        lh = leading if leading is not None else 9 * scale
        for ln in wrap_text(s, scale, max_width):
            self.text(x, y, ln, scale, color)
            y += lh
        return y


def encode_png(canvas):
    """Deterministic PNG encoding of the canvas (zlib, filter None)."""
    raw = bytearray()
    stride = canvas.w * 3
    for yy in range(canvas.h):
        raw.append(0)
        raw += canvas.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# --- little pictograms ----------------------------------------------------
def draw_skyline(c, x, y, w, h):
    """A city skyline at night: dark towers, lit windows, two blasts."""
    c.fill(x, y + h - 6, w, 6, NAVY)  # ground
    towers = [(0, 62, 34), (40, 88, 30), (76, 52, 36), (118, 96, 28),
              (152, 70, 32)]
    for dx, th, tw in towers:
        c.fill(x + dx, y + h - 6 - th, tw, th, NAVY)
        for wy in range(y + h - 6 - th + 8, y + h - 12, 14):
            for wx in range(x + dx + 5, x + dx + tw - 4, 10):
                if (wx + wy) % 3 == 0:
                    c.fill(wx, wy, 3, 4, GOLD)
    c.burst(x + 58, y + 18, 26, ORANGE)
    c.burst(x + 58, y + 18, 14, RED)
    c.burst(x + 136, y + 30, 20, ORANGE)
    c.burst(x + 136, y + 30, 11, RED)


def draw_tower(c, x, y, w, h):
    """A tall skyscraper with a strike flash near its crown."""
    c.fill(x + w // 2 - 4, y, 8, h, NAVY)
    c.fill(x, y + h // 3, w, h - h // 3, NAVY)
    for wy in range(y + h // 3 + 8, y + h - 8, 12):
        c.fill(x + 6, wy, w - 12, 3, GOLD)
    c.burst(x + w - 6, y + 14, 22, ORANGE)
    c.burst(x + w - 6, y + 14, 12, RED)
    c.fill(x - 6, y + h - 4, w + 12, 4, NAVY)


def draw_tanker(c, x, y, w, h):
    """An oil tanker on the sea, with a smoke plume from a fire."""
    c.fill(x, y + h - 14, w, 6, SKY)  # sea line
    c.fill(x + 6, y + h // 2, w - 12, h // 2 - 14, RED)  # hull
    c.fill(x + 6, y + h // 2 - 10, w - 12, 10, NAVY)     # deck
    for k in range(4):
        c.fill(x + 16 + k * (w // 5), y + h // 2 - 26,
               w // 6, 16, NAVY)  # containers
    c.fill(x + w - 22, y + h // 2 - 34, 8, 34, INK)  # funnel
    c.disc(x + w // 3, y + 10, 12, GREY)   # smoke
    c.disc(x + w // 3 + 8, y + 22, 16, GREY)
    c.disc(x + w // 3 - 6, y + 26, 10, GREY)
    c.burst(x + w // 3, y + h // 2 - 30, 18, ORANGE)
    c.burst(x + w // 3, y + h // 2 - 30, 10, RED)


def draw_storm(c, x, y, w, h):
    """A cyclone: spiral cloud bands over rain streaks."""
    c.disc(x + w // 2, y + h // 3, 34, SKY)
    c.ring(x + w // 2, y + h // 3, 34, NAVY, 3)
    c.disc(x + w // 2 - 12, y + h // 3 - 6, 12, CARD)
    c.disc(x + w // 2 + 12, y + h // 3 + 6, 12, CARD)
    c.disc(x + w // 2, y + h // 3, 6, GOLD)
    for k in range(6):
        xx = x + 10 + k * (w - 20) // 6
        c.segment(xx, y + 2 * h // 3, xx - 6, y + h - 6, SKY)


# --- the front page ---------------------------------------------------------
def build_png():
    c = Canvas(W, H, PAPER)

    # Masthead: navy band, paper name, the date in large type.
    c.fill(0, 0, W, 124, NAVY)
    c.text_mid(W // 2, 16, "THE WORLD IN ONE IMAGE", 3, GOLD)
    c.text_mid(W // 2, 52, "FRIDAY 20 NOVEMBER 2026", 6, CARD)
    c.hrule(0, 106, W, GOLD, 3)
    c.fill(0, 116, W, 8, RED)

    # Lead story: Russia's overnight missile attack on Kyiv.
    c.text(36, 148, "UKRAINE * OVERNIGHT ATTACK", 3, RED)
    c.text(36, 190, "RUSSIA HITS KYIV", 7, INK)
    c.text(36, 246, "IN NIGHT ATTACK", 7, INK)
    y = c.para(36, 322, "OVERNIGHT MISSILE AND DRONE STRIKE ON "
               "THE CAPITAL; DEBRIS SETS BUILDING ABLAZE IN "
               "OBOLONSKYI DISTRICT; EU TO SUMMON RUSSIAN ENVOY",
               3, INK, 700, leading=27)
    c.text(36, 440, "FOLLOWS THURSDAY'S THREE-WAY SUMMIT IN SHENZHEN",
           2, GREY)
    draw_skyline(c, 790, 270, 180, 140)
    c.hrule(36, 486, 952, INK, 2)

    # Middle row: the Houthi strike on Riyadh and the Hormuz tanker.
    c.text(36, 508, "SAUDI ARABIA * RIYADH", 3, RED)
    c.text(36, 544, "HOUTHI MISSILE", 5, INK)
    c.text(36, 586, "HITS PIF TOWER", 5, INK)
    c.para(36, 640, "SAUDI AIR DEFENCES INTERCEPT MORE MISSILES "
           "AND DRONES", 3, INK, 460, leading=27)
    draw_tower(c, 410, 724, 56, 56)
    c.vrule(512, 500, 270, LINE, 2)

    c.text(528, 508, "STRAIT OF HORMUZ", 3, RED)
    c.text(528, 544, "TANKER ON FIRE", 5, INK)
    c.text(528, 586, "AFTER MINE HIT", 5, INK)
    c.para(528, 640, "TANKER CATCHES FIRE AFTER HITTING A MINE; "
           "UKMTO WARNS SHIPS", 3, INK, 460, leading=27)
    draw_tanker(c, 820, 724, 140, 56)
    c.hrule(36, 786, 952, INK, 2)

    # Bottom row: three short cards.
    cards = [
        (36, "EUROPE", "EU AND UK MEET", "IN BRUSSELS",
         "SECOND SUMMIT SINCE RENEWED TIES; EU ADOPTS 1BN EURO AID"),
        (364, "MARKETS", "STOCKS SLIDE", "AGAIN",
         "S&P 500 DOWN 2 PERCENT; NIKKEI DOWN 4.8 PERCENT"),
        (692, "ASIA", "CYCLONE AKVAN", "HITS ODISHA",
         "LANDFALL IN INDIA BRINGS HEAVY RAIN AND STRONG WINDS"),
    ]
    for x, kicker, h1, h2, sub in cards:
        c.fill(x, 800, 296, 150, CARD)
        c.fill(x, 800, 296, 4, RED)
        c.fill(x, 800, 4, 150, LINE)
        c.fill(x + 292, 800, 4, 150, LINE)
        c.fill(x, 946, 296, 4, LINE)
        c.text(x + 16, 814, kicker, 2, RED)
        c.text(x + 16, 838, h1, 3, INK)
        c.text(x + 16, 865, h2, 3, INK)
        c.para(x + 16, 894, sub, 2, GREY, 264, leading=18)

    # Footer ticker: the rest of the day, in one strip.
    c.fill(0, 962, W, 62, NAVY)
    c.text_mid(W // 2, 966,
               "ALSO: KENYA EBOLA-FREE COUNTDOWN BEGINS * HAITI: 34 "
               "KILLED * SENEGAL BOAT SINKS", 2, CARD)
    c.text_mid(W // 2, 984,
               "US SENATE PASSES ENERGY BILL 62-33 * ANTHROPIC "
               "SLIDES AFTER RECORD IPO", 2, CARD)
    c.text_mid(W // 2, 1002,
               "ITALY FINES META 805M EURO * MERZ REJECTS YALTA "
               "DEAL * SUDAN STRIKE KILLS 10", 2, CARD)
    return encode_png(c)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = build_png()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
