from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from texfury import Texture, BCFormat

ROOT = Path.cwd()
OUT = ROOT / 'build_output' / 'fl_overlay_src'
OUT.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    r'C:\Windows\Fonts\arialbd.ttf',
    r'C:\Windows\Fonts\segoeuib.ttf',
    r'C:\Windows\Fonts\arial.ttf',
]

def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

BLUE = (0, 72, 168, 255)
DARK = (0, 35, 105, 255)
WHITE = (248, 250, 252, 255)
CYAN = (45, 180, 235, 255)

def side_texture():
    w, h = 2048, 512
    im = Image.new('RGBA', (w, h), BLUE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 34), fill=DARK)
    d.rectangle((0, h-34, w, h), fill=DARK)
    for start in (0, 1620):
        for i in range(6):
            x = start + i * 78
            col = WHITE if i % 2 == 0 else CYAN
            d.polygon([(x, 0), (x+52, 0), (x+146, h), (x+94, h)], fill=col)
    d.rounded_rectangle((430, 66, 1615, 446), radius=38, fill=(245, 248, 252, 255))
    f = font(142)
    text = 'CELNÍ SPRÁVA'
    bb = d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    d.text(((w-tw)//2, 185-th//2), text, font=f, fill=(10, 24, 48, 255))
    f2 = font(47)
    sub = 'CUSTOMS  •  ZOLL  •  DOUANE'
    bb = d.textbbox((0, 0), sub, font=f2)
    d.text(((w-(bb[2]-bb[0]))//2, 322), sub, font=f2, fill=(18, 55, 106, 255))
    im.save(OUT / 'cs_side.png')

def hood_texture():
    w, h = 1024, 1024
    im = Image.new('RGBA', (w, h), BLUE)
    d = ImageDraw.Draw(im)
    d.polygon([(170, 120), (854, 120), (720, 900), (304, 900)], fill=WHITE)
    d.polygon([(245, 180), (779, 180), (680, 820), (344, 820)], fill=(244,247,251,255))
    f = font(96)
    y = 330
    for line in ('CELNÍ','SPRÁVA'):
        bb = d.textbbox((0,0), line, font=f)
        d.text(((w-(bb[2]-bb[0]))//2, y), line, font=f, fill=(10, 24, 48, 255))
        y += 125
    im.save(OUT / 'cs_hood.png')

def rear_texture():
    w, h = 1024, 256
    im = Image.new('RGBA', (w, h), BLUE)
    d = ImageDraw.Draw(im)
    for i in range(5):
        x = i*74
        d.polygon([(x,0),(x+46,0),(x+105,h),(x+59,h)], fill=WHITE if i%2==0 else CYAN)
    f = font(82)
    text='CELNÍ SPRÁVA'
    bb=d.textbbox((0,0),text,font=f)
    d.rounded_rectangle((350,32,990,224), radius=28, fill=WHITE)
    d.text((670-(bb[2]-bb[0])//2, 115-(bb[3]-bb[1])//2), text, font=f, fill=(10,24,48,255))
    im.save(OUT / 'cs_rear.png')

side_texture(); hood_texture(); rear_texture()

# Sollumz native export expects packed embedded textures to already be DDS.
for png in sorted(OUT.glob('cs_*.png')):
    tex = Texture.from_image(
        str(png),
        format=BCFormat.BC1,
        quality=0.85,
        generate_mipmaps=True,
        min_mip_size=4,
        resize_to_pot=True,
        name=png.stem,
    )
    tex.save_dds(str(png.with_suffix('.dds')))

print('FL LIVERY TEXTURES READY', [p.name for p in OUT.glob('cs_*')])
