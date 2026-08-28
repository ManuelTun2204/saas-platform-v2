import os, subprocess
from imageio_ffmpeg import get_ffmpeg_exe

BASE = r"C:\projects\saas-platform-v2\cliente-demo"
SLIDES = os.path.join(BASE, "slides")
WORK = os.path.join(BASE, "video_work")
MUSIC = os.path.join(WORK, "musica_up.wav")
W, H = 1280, 720
FPS = 30
DUR = 4.5
XFADE = 1.0
FF = get_ffmpeg_exe()

slides = ["n1.png","n2.png","n3.png","n4.png","n5.png","n6.png","n7.png","n8.png"]
n = len(slides)
frames = int(DUR*FPS)
clips = []

# 1. crear cada clip limpio con zoompan y -frames:v (corta la duracion exacta)
for i, s in enumerate(slides):
    path = os.path.join(SLIDES, s)
    f = os.path.join(WORK, f"c{i}.mp4")
    if os.path.exists(f):
        os.remove(f)
    z = ("zoompan=z='min(zoom+0.0014,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
         "d={}:s={}x{}:fps={}".format(frames, W, H, FPS)) if i % 2 == 0 else \
        ("zoompan=z='max(1.18-0.0014*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
         "d={}:s={}x{}:fps={}".format(frames, W, H, FPS))
    vf = z + ",format=yuv420p"
    cmd = [FF, "-y", "-i", path, "-vf", vf, "-frames:v", str(frames), f]
    r = subprocess.run(cmd, capture_output=True, text=True)
    clips.append(f)
    print("clip", i, "ok" if r.returncode==0 else "ERR", os.path.getsize(f) if os.path.exists(f) else 0)

# 2. ensamblar con crossfades + musica
total_dur = n*DUR + (n-1)*XFADE
parts = []
prev = "0:v"
for i in range(1, n):
    offset = i*(DUR - XFADE)
    parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={offset:.2f}[x{i}]")
    prev = f"x{i}"
fc = ";".join(parts) + f";[{prev}]format=yuv420p[outv]"
fc += f";[{n}:a]afade=t=in:d=1,afade=t=out:st={total_dur-2.5:.1f}:d=2.5,volume=1.0[a]"

cmd = [FF, "-y"]
for f in clips:
    cmd += ["-i", f]
cmd += ["-i", MUSIC, "-filter_complex", fc, "-map", "[outv]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p", os.path.join(BASE, "video-demo-final.mp4")]
print("ensamblando...")
r = subprocess.run(cmd, capture_output=True, text=True)
print("returncode:", r.returncode)
if r.returncode != 0:
    print(r.stderr[-1200:])
else:
    p = os.path.join(BASE, "video-demo-final.mp4")
    print("VIDEO OK:", p, os.path.getsize(p))
