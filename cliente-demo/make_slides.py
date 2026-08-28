import os, subprocess, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"C:\projects\saas-platform-v2\cliente-demo"
CAP = os.path.join(BASE, "capturas")
OUT = os.path.join(BASE, "slides")
WORK = os.path.join(BASE, "video_work")
W, H = 1280, 720
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(os.path.join("C:/Windows/Fonts", name), size)

def gradient_bg(w, h, c1=(37,99,235), c2=(118,75,162)):
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / h
        img.putpixel((0, y), (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t)))
    return img.resize((w, h))

def center_text(draw, box, text, fnt, fill, y, spacing=14, maxw=None):
    lines = []
    for line in text.split("\n"):
        lines.append(line)
    total = 0
    for ln in lines:
        total += draw.textlength(ln, font=fnt)
    x = (box[0]+box[2])//2 - int(total/len(lines))//2 if len(lines)>1 else (box[0]+box[2])//2
    # simpler per-line centering
    cy = y
    for ln in lines:
        wln = draw.textlength(ln, font=fnt)
        draw.text(((box[0]+box[2]-wln)/2, cy), ln, font=fnt, fill=fill)
        cy += fnt.size + spacing

def rounded_card(img, box, radius, fill):
    ov = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, radius=radius, fill=fill)
    img.paste(ov, (0,0), ov)

def title_card(fname, kicker, title, sub):
    img = gradient_bg(W, H, (15,23,42), (30,58,138))
    d = ImageDraw.Draw(img)
    # decorative glow
    glow = Image.new("RGBA", (W,H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W-560, -260, W+80, 380), fill=(59,130,246,70))
    gd.ellipse((-240, H-200, 300, H+200), fill=(139,92,246,70))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.paste(glow, (0,0), glow)
    d = ImageDraw.Draw(img)
    # kicker
    kk = font(26, True).getbbox(kicker)
    kw = d.textlength(kicker, font=font(26, True))
    kx = (W-kw)/2
    # pill
    img2 = Image.new("RGBA", img.size, (0,0,0,0))
    d2 = ImageDraw.Draw(img2)
    d2.rounded_rectangle((kx-22, 150, kx+kw+22, 212), radius=31, fill=(255,255,255,30))
    img.paste(img2, (0,0), img2)
    d = ImageDraw.Draw(img)
    d.text((kx, 161), kicker, font=font(26, True), fill=(147,197,253))
    # title
    d.text((0,0), "", font=font(1))
    draw_title(img, title, 275)
    # sub
    d = ImageDraw.Draw(img)
    sub_f = font(34)
    lines = sub.split("\n") if isinstance(sub, str) else sub
    y = 520
    for ln in lines:
        wl = d.textlength(ln, font=sub_f)
        d.text(((W-wl)/2, y), ln, font=sub_f, fill=(203,213,225))
        y += sub_f.size + 12
    img.save(os.path.join(OUT, fname))

def draw_title(img, text, y):
    fnt = font(74, True)
    d = ImageDraw.Draw(img)
    lines = text.split("\n")
    cy = y
    for ln in lines:
        w = d.textlength(ln, font=fnt)
        x = (W-w)/2
        d.text((x+3, cy+3), ln, font=fnt, fill=(0,0,0,120))
        d.text((x, cy), ln, font=fnt, fill=(255,255,255))
        cy += fnt.size + 16

def photo_card(fname, src_img, label, sub=""):
    img = Image.open(src_img).convert("RGB")
    # resize to fit 1280x720 by cover
    ratio = max(W/img.width, H/img.height)
    img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)
    x = (img.width-W)//2; y = (img.height-H)//2
    img = img.crop((x, y, x+W, y+H))
    # dim slightly + bottom gradient for text
    ov = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(ov)
    for yy in range(H-260, H):
        a = int(210*(yy-(H-260))/260)
        d.line([(0,yy),(W,yy)], fill=(10,17,36,a))
    img.paste(ov, (0,0), ov)
    d = ImageDraw.Draw(img)
    if label:
        fnt = font(46, True)
        w = d.textlength(label, font=fnt)
        d.text(((W-w)/2, H-190), label, font=fnt, fill=(255,255,255))
    if sub:
        fnt2 = font(28)
        w2 = d.textlength(sub, font=fnt2)
        d.text(((W-w2)/2, H-120), sub, font=fnt2, fill=(203,213,225))
    img.save(os.path.join(OUT, fname))

# ---- Build slides ----
title_card("s1.png", "DEMO REAL · RESTAURANTE", "Tu negocio merece estar\nen internet", ["Una pagina web profesional, chatbot de IA", "y app para tu celular, atendiendo por ti."])
photo_card("s2.png", os.path.join(CAP,"01-web-full.png"), "Tu pagina web profesional", "Generada con IA en minutos, lista para el mundo")
title_card("s3.png", "ATIENDE 24/7", "Un asistente que nunca duerme", ["Chatbot de IA con los datos reales de tu negocio", "WhatsApp flotante · captura correos · nunca pierdes una venta"])
photo_card("s4.png", os.path.join(CAP,"02-web-movil.png"), "Perfecta en cualquier pantalla", "Web adaptable a celular y computadora")
title_card("s5.png", "ADMINISTRA DESDE TU CELULAR", "Tu negocio en tu bolsillo", ["Dashboard de pedidos, leads y estadisticas", "Editables sin saber programar, instalable como app"])
photo_card("s6.png", os.path.join(CAP,"03-app-cliente.png"), "App movil del negocio", "Pedidos, clientes y control donde vayas")
title_card("s7.png", "TU OPORTUNIDAD ES HOY", "No pierdas mas clientes", ["Presencia profesional sin desarrollo caro", "Membresia mensual · nosotros nos encargamos de todo"])

print("Slides creados:", sorted(os.listdir(OUT)))
