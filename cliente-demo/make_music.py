import numpy as np, wave, os

SR = 44100
DUR = 40.0
BASE = r"C:\projects\saas-platform-v2\cliente-demo"
OUT = os.path.join(BASE, "video_work", "musica_up.wav")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Progresion alegre/moderna: C - G - Am - F (upbeat pop)
C4=261.63; D4=293.66; E4=329.63; F4=349.23; G4=392.00; A4=440.00; B4=493.88
C5=523.25; D5=587.33; E5=659.25; F5=698.46; G5=783.99; A5=880.00
C3=130.81; G2=98.00; A2=110.00; F2=87.31   # bajos
E3=164.81; G3=196.00; A3=220.00; F3=174.61

# estructura: cambios cada 4s -> 10 acordes en 40s
prog = [
    ["C",  C4,E4,G4,C5, C3],
    ["G",  G3,B4,D5,G4, G2],
    ["Am", A4,C5,E5,A4, A2],
    ["F",  F4,A4,C5,F4, F3],
    ["C",  C4,E4,G4,C5, C3],
    ["G",  G3,B4,D5,G4, G2],
    ["F",  F4,A4,C5,F4, F3],
    ["G",  G3,B4,D5,G4, G2],
    ["C",  C4,E4,G4,C5, C3],
    ["C",  C4,E4,G4,C5, C3],
]
CHANGE = DUR / len(prog)

def env_pluck(t, dur):
    return np.minimum(1, t/0.005) * np.exp(-3.0*t/dur)

def note(freq, duration, sr=SR, bright=True):
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    if bright:
        # piano-alegre con brillo (mas armonicos)
        sig = (np.sin(2*np.pi*freq*t) + 0.6*np.sin(2*np.pi*freq*2*t)
               + 0.35*np.sin(2*np.pi*freq*3*t) + 0.15*np.sin(2*np.pi*freq*4*t))
    else:
        sig = (np.sin(2*np.pi*freq*t) + 0.3*np.sin(2*np.pi*freq*2*t))
    return env_pluck(t, duration)*sig

def bass(freq, duration, sr=SR):
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    return (np.sin(2*np.pi*freq*t) + 0.4*np.sin(2*np.pi*freq*2*t)) * env_pluck(t, duration)

def mix(arr, out, vol=1.0):
    n = min(len(out), len(arr))
    out[:n] = out[:n] + vol*arr[:n]

track = np.zeros(int(SR*DUR))

for ci, ch in enumerate(prog):
    notes = ch[1:-1]
    bass_n = ch[-1]
    start = ci*CHANGE
    mel_dur = CHANGE*0.95
    # arpegio rapido (8vas de la melodia) - dinamico
    seq = notes*2
    step = 0.30
    for si, f in enumerate(seq):
        s0 = start + si*step
        if s0 >= DUR: break
        seg = note(f, min(step*1.35, CHANGE-si*step))
        ss = int(s0*SR)
        seg = seg[:max(0, int(SR*DUR)-ss)]
        mix(seg, track[ss:], vol=0.42)
    # bajo en la pulsacion (4 por cambio)
    for b in range(4):
        bs = start + b*(CHANGE/4)
        seg = bass(bass_n, CHANGE/4*0.9)
        ss = int(bs*SR); seg = seg[:max(0, int(SR*DUR)-ss)]
        mix(seg, track[ss:], vol=0.35)

# normalizar (dejar algo de pico) y volumen medio-bajo (fondo)
track = track / (np.max(np.abs(track))+1e-9) * 0.30
fade = int(2.0*SR)
track[:fade] *= np.linspace(0,1,fade)
track[-int(2.5*SR):] *= np.linspace(1,0,int(2.5*SR))

pcm = (track*32767).astype(np.int16)
with wave.open(OUT, "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("musica alegre generada:", OUT, os.path.getsize(OUT), "bytes")
