import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"C:\projects\saas-platform-v2\cliente-demo"
CAP = os.path.join(BASE, "capturas")
OUT = os.path.join(BASE, "slides")
W, H = 1280, 720
os.makedirs(OUT, exist_ok=True)

def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(os.path.join("C:/Windows/Fonts", name), size)

def gradient_bg(w, h, c1=(15,23,42), c2=(30,58,138)):
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / h
        img.putpixel((0, y), (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t)))
    return img.resize((w, h))

def glow_layer():
    glow = Image.new("RGBA", (W,H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W-540, -240, W+120, 420), fill=(59,130,246,90))
    gd.ellipse((-260, H-220, 320, H+220), fill=(139,92,246,90))
    return glow.filter(ImageFilter.GaussianBlur(70))

def draw_multiline_center(img, box, lines, fnt, fill, y, spacing=10):
    d = ImageDraw.Draw(img)
    cy = y
    for ln in lines:
        wl = d.textlength(ln, font=fnt)
        d.text(((box[0]+box[2]-wl)/2, cy), ln, font=fnt, fill=fill)
        cy += fnt.size + spacing
    return cy

def title_card(fname, kicker, title_lines, sub_lines, accent=(59,130,246,139,92,246)):
    img = gradient_bg(W, H, (10,18,38), (28,52,120))
    gl = glow_layer(); img.paste(gl, (0,0), gl)
    d = ImageDraw.Draw(img)
    # kicker pill
    kf = font(30, True)
    kw = d.textlength(kicker, font=kf)+52
    img2 = Image.new("RGBA", img.size, (0,0,0,0))
    d2 = ImageDraw.Draw(img2)
    d2.rounded_rectangle(((W-kw)/2, 130, (W+kw)/2, 196), radius=33, fill=(255,255,255,28))
    img.paste(img2, (0,0), img2)
    d = ImageDraw.Draw(img)
    d.text(((W-kw+26)/2, 146), kicker, font=kf, fill=(147,197,253))
    # title (bigger, bold)
    tf = font(78, True)
    cy = draw_multiline_center(img, (0,0,W,H), title_lines, tf, (255,255,255), 250, 10)
    # subtitle
    sf = font(34)
    draw_multiline_center(img, (0,0,W,H), sub_lines, sf, (203,213,225), cy+40, 12)
    img.save(os.path.join(OUT, fname))

def photo_card(fname, src_img, label, sub=""):
    img = Image.open(src_img).convert("RGB")
    ratio = max(W/img.width, H/img.height)
    img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)
    x = (img.width-W)//2; y = (img.height-H)//2
    img = img.crop((x, y, x+W, y+H))
    ov = Image.new("RGBA", (W,H), (0,0,0,0))
    d = ImageDraw.Draw(ov)
    for yy in range(H-250, H):
        a = int(205*(yy-(H-250))/250)
        d.line([(0,yy),(W,yy)], fill=(8,14,32,a))
    img.paste(ov, (0,0), ov)
    d = ImageDraw.Draw(img)
    if label:
        fnt = font(50, True)
        w = d.textlength(label, font=fnt)
        d.text(((W-w)/2, H-185), label, font=fnt, fill=(255,255,255))
    if sub:
        fnt2 = font(28)
        w2 = d.textlength(sub, font=fnt2)
        d.text(((W-w2)/2, H-115), sub, font=fnt2, fill=(203,213,225))
    img.save(os.path.join(OUT, fname))

def chat_mockup(fname):
    """Chatbot en accion: conversacion realista con burbujas."""
    img = gradient_bg(W, H, (8,14,30), (20,40,90))
    gl = glow_layer(); img.paste(gl, (0,0), gl)
    # header bar of the widget
    hdr = Image.new("RGBA", (W,96), (0,0,0,0))
    dh = ImageDraw.Draw(hdr)
    dh.rectangle((0,0,W,96), fill=(30,64,175,255))
    # avatar circle
    dh.ellipse((40,24,88,72), fill=(255,255,255,255))
    dh.text((50,40), "C", font=font(26, True), fill=(30,64,175))
    dh.text((104,36), "Casa Sabor · en línea", font=font(28, True), fill=(255,255,255))
    dh.text((104,70), "Asistente de tu restaurante", font=font(19), fill=(191,219,254))
    img.paste(hdr, (0,0), hdr)
    d = ImageDraw.Draw(img)
    # messages (user right blue, bot left gray)
    msgs = [
        ("bot", "¡Hola! ¿Qué te gustaría comer hoy? 😊"),
        ("user", "¿Qué tienen de especial?"),
        ("bot", "Hoy recomendamos el plato del día: cochinita pibil con frijol colado. ¿Te armo tu pedido para recoger o delivery? 🛵"),
        ("user", "A una, delivery a mi casa a las 8"),
        ("bot", "¡Listo! Te confirmo para las 8:00 p.m. ¿Tu correo para enviarte el ticket? 📩"),
    ]
    y = 140
    for who, text in msgs:
        fnt = font(30)
        tf = font(30)
        wbox = min(int(d.textlength(text, font=tf)+60), 1000)
        x0 = 60 if who=="bot" else W-60-wbox
        x1 = 60+wbox if who=="bot" else W-60
        color = (36,46,70,255) if who=="bot" else (37,99,235,255)
        tcol = (226,232,240) if who=="bot" else (255,255,255)
        # bubble
        bub = Image.new("RGBA", (W,H), (0,0,0,0))
        db = ImageDraw.Draw(bub)
        db.rounded_rectangle((x0, y, x1, y+78), radius=22, fill=color)
        img.paste(bub, (0,0), bub)
        d = ImageDraw.Draw(img)
        d.text((x0+24, y+22), text, font=fnt, fill=tcol)
        y += 92
    img.save(os.path.join(OUT, fname))

# ---- slides ----
if __name__ == "__main__":
    # 1 intro
    title_card("n1.png", "TU NEGOCIO EN INTERNET", ["Tu restaurante,", "abierto 24/7"], ["Sitio web + chatbot de IA + app para tu celular", "Atendiendo a tus clientes incluso mientras duermes"])
    # 2 web
    photo_card("n2.png", os.path.join(CAP,"01-web-full.png"), "Tu web profesional", "Generada con IA en minutos, lista para el mundo")
    # 3 chatbot
    chat_mockup("n3.png")
    # 4 reporte seo
    photo_card("n4.png", os.path.join(CAP,"05-reporte-seo.png"), "Aparece en Google", "Reporte SEO: tus clientes te encuentran primero")
    # 5 movil web
    photo_card("n5.png", os.path.join(CAP,"02-web-movil.png"), "Perfecta en tu celular", "Diseño adaptable a cualquier pantalla")
    # 6 ganancias (chart)
    def ganancias_card():
        img = gradient_bg(W, H, (10,18,38), (20,50,110))
        gl = glow_layer(); img.paste(gl, (0,0), gl)
        d = ImageDraw.Draw(img)
        d.text((60,60), "TUS GANANCIAS CREEN", font=font(40, True), fill=(52,211,153))
        ch = Image.open(os.path.join(OUT,"s_chart_ganancias.png")).convert("RGBA")
        ch = ch.resize((1000, 560), Image.LANCZOS)
        img.paste(ch, ((W-1000)//2, 150), ch)
        d = ImageDraw.Draw(img)
        w = d.textlength("Cada cliente en línea = más ventas para ti", font=font(30))
        d.text(((W-w)/2, 22), "Cada cliente en línea = más ventas para ti", font=font(30), fill=(203,213,225))
        img.save(os.path.join(OUT,"n6.png"))
    ganancias_card()
    # 7 app cliente
    photo_card("n7.png", os.path.join(CAP,"03-app-cliente.png"), "Controla todo desde tu celular", "Pedidos, clientes y estadísticas donde vayas")
    # 8 cierre
    title_card("n8.png", "TU OPORTUNIDAD ES HOY", ["No pierdas más clientes"], ["Presencia profesional sin desarrollo caro", "Membresía mensual · nosotros nos encargamos de todo"])
    print("slides:", sorted([f for f in os.listdir(OUT) if f.startswith("n")]))
