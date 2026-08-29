import os, subprocess
from imageio_ffmpeg import get_ffmpeg_exe

BASE = r"C:\projects\saas-platform-v2\cliente-demo"
SLIDES = os.path.join(BASE, "slides")
WORK = os.path.join(BASE, "video_work")
MUSIC = os.path.join(WORK, "pista-video.mp3")
W, H = 1080, 1920
FPS = 30
DUR = 4.5
XFADE = 1.0
FF = get_ffmpeg_exe()

slides = ["n1.png", "n2.png", "n3.png", "n4.png", "n5.png", "n6.png", "n7.png", "n8.png"]
n = len(slides)
frames = int(DUR * FPS)
clips = []

for i, s in enumerate(slides):
    path = os.path.join(SLIDES, s)
    f = os.path.join(WORK, f"v{i}.mp4")
    if os.path.exists(f):
        os.remove(f)
    zoom = ("zoompan=z='min(zoom+0.0014,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d={}:s={}x{}:fps={}".format(frames, W, H, FPS)) if i % 2 == 0 else \
           ("zoompan=z='max(1.18-0.0014*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            "d={}:s={}x{}:fps={}".format(frames, W, H, FPS))
    # fondo desenfocado + slide en cover, con el zoom animado encima
    vf = (f"split=2[bg][fg];"
          f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"boxblur=luma_radius=30:luma_power=2[bgblur];"
          f"[fg]scale={W}:{H}:force_original_aspect_ratio=increase[fgfull];"
          f"[bgblur][fgfull]overlay=0:0,{zoom},format=yuv420p")
    cmd = [FF, "-y", "-i", path, "-vf", vf, "-frames:v", str(frames), f]
    r = subprocess.run(cmd, capture_output=True, text=True)
    clips.append(f)
    print("clip", i, "ok" if r.returncode == 0 else "ERR",
          os.path.getsize(f) if os.path.exists(f) else 0)

total_dur = n * DUR + (n - 1) * XFADE
parts = []
prev = "0:v"
for i in range(1, n):
    offset = i * (DUR - XFADE)
    parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={offset:.2f}[x{i}]")
    prev = f"x{i}"
fc = ";".join(parts) + f";[{prev}]format=yuv420p[outv]"
fc += f";[{n}:a]atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=0.4,afade=t=out:st={total_dur-1.8:.1f}:d=1.8,volume=1.0[a]"

cmd = [FF, "-y"]
for f in clips:
    cmd += ["-i", f]
cmd += ["-i", MUSIC, "-filter_complex", fc, "-map", "[outv]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p", os.path.join(BASE, "video-demo-whatsapp.mp4")]
print("ensamblando whatsapp...")
r = subprocess.run(cmd, capture_output=True, text=True)
print("returncode:", r.returncode)
if r.returncode != 0:
    print(r.stderr[-1500:])
else:
    p = os.path.join(BASE, "video-demo-whatsapp.mp4")
    print("VIDEO OK:", p, os.path.getsize(p))
