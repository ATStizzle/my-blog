"""Make a 1080x1920 Instagram Story image for New York Tints.

Usage:
  python tools/make_story.py OUT.jpg "Kicker" "Headline" "Body text" "Call to action"

Text wraps automatically. Keep the headline short (under ~60 characters).
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG = (17, 17, 17)          # site ink color
COPPER = (196, 122, 64)    # copper accent
WHITE = (255, 255, 255)
GREY = (190, 190, 190)
FONT_DIR = "/usr/share/fonts/opentype/inter/"


def font(weight, size):
    return ImageFont.truetype(f"{FONT_DIR}Inter-{weight}.otf", size)


def wrap(draw, text, fnt, max_w):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=fnt) <= max_w:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def block(draw, y, text, fnt, color, gap, max_w=W - 200):
    for ln in wrap(draw, text, fnt, max_w):
        draw.text((100, y), ln, font=fnt, fill=color)
        y += fnt.size + gap
    return y


def main(out, kicker, headline, body, cta):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # top brand bar
    d.text((100, 170), "NEW YORK TINTS", font=font("ExtraBold", 40), fill=WHITE)
    d.rectangle([100, 235, 220, 243], fill=COPPER)

    y = 560
    y = block(d, y, kicker.upper(), font("Bold", 38), COPPER, 14)
    y += 30
    y = block(d, y, headline, font("ExtraBold", 92), WHITE, 18)
    y += 50
    y = block(d, y, body, font("Regular", 46), GREY, 20)

    # call to action button
    f = font("Bold", 46)
    tw = d.textlength(cta, font=f)
    bx, by = 100, H - 520
    d.rounded_rectangle([bx, by, bx + tw + 100, by + 120], radius=24, fill=COPPER)
    d.text((bx + 50, by + 34), cta, font=f, fill=WHITE)

    d.text((100, H - 300), "nytints.com  ·  (718) 968-8866", font=font("SemiBold", 40), fill=WHITE)
    d.text((100, H - 240), "Brooklyn, NY", font=font("Regular", 36), fill=GREY)

    img.save(out, "JPEG", quality=90, optimize=True)


if __name__ == "__main__":
    main(*sys.argv[1:6])
