# ytweb.py
from flask import Flask, request, redirect
from pathlib import Path
import subprocess
import threading
import shutil
import uuid

app = Flask(__name__)

MUSIC_DIR = Path.home() / 'Music' / 'DiscoDownload'
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

FFMPEG_OK = shutil.which('ffmpeg') is not None
if not FFMPEG_OK:
    print('WARNING: ffmpeg not found - audio will download as webm/opus, not mp3/wav.')
    print('Fix: winget install ffmpeg')

_FFMPEG_WARN = (
    '<p class="msg" style="border-left-color:#FF9900;color:#FF9900;margin-bottom:20px">'
    'ffmpeg no encontrado - los archivos se descargarán como webm/opus en vez de mp3/wav. '
    'Solución: <code style="font-family:monospace;background:rgba(0,0,0,.3);'
    'padding:2px 5px;border-radius:2px">winget install ffmpeg</code>'
    '</p>'
)

# job store: run_id -> {'tracks': [...], 'fmt': str}
_jobs: dict = {}
_lock = threading.Lock()


def _analyze_bpm(filepath: str) -> float | None:
    try:
        import librosa
        y, sr = librosa.load(filepath, sr=22050, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, '__len__') else float(tempo)
        return round(bpm, 1)
    except Exception:
        return None


def _embed_bpm(filepath: str, bpm: float) -> None:
    try:
        if filepath.lower().endswith('.mp3'):
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TBPM
            audio = MP3(filepath, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(TBPM(encoding=3, text=str(int(bpm))))
            audio.save()
    except Exception:
        pass


def _download(run_id: str, idx: int, url: str, fmt: str, full_playlist: bool) -> None:
    with _lock:
        _jobs[run_id]['tracks'][idx]['status'] = 'running'
    try:
        cmd = ['yt-dlp', '--print', 'after_move:%(filepath)s']
        if not full_playlist:
            cmd.append('--no-playlist')
        cmd += ['-x', '--audio-format', fmt, '--audio-quality', '0',
                '-o', str(MUSIC_DIR / '%(title)s.%(ext)s'), url]
        r = subprocess.run(cmd, capture_output=True, text=True)

        if r.returncode == 0:
            # --print outputs one filepath per track to stdout
            filepaths = [l.strip() for l in r.stdout.splitlines()
                         if l.strip() and Path(l.strip()).is_file()]

            if filepaths:
                with _lock:
                    _jobs[run_id]['tracks'][idx]['status'] = 'analyzing'
                    _jobs[run_id]['tracks'][idx]['track_count'] = len(filepaths)

                bpms = []
                for fp in filepaths:
                    bpm = _analyze_bpm(fp)
                    if bpm is not None:
                        _embed_bpm(fp, bpm)
                        bpms.append(bpm)

                with _lock:
                    t = _jobs[run_id]['tracks'][idx]
                    t['status'] = 'done'
                    if bpms:
                        if len(bpms) == 1:
                            t['bpm'] = bpms[0]
                        else:
                            t['bpm_avg'] = round(sum(bpms) / len(bpms), 1)
                            t['bpm_count'] = len(filepaths)
            else:
                with _lock:
                    _jobs[run_id]['tracks'][idx]['status'] = 'done'
        else:
            with _lock:
                t = _jobs[run_id]['tracks'][idx]
                t['status'] = 'error'
                lines = [l.strip() for l in r.stderr.splitlines() if l.strip()]
                t['error'] = lines[-1] if lines else 'Error desconocido'
    except FileNotFoundError:
        with _lock:
            t = _jobs[run_id]['tracks'][idx]
            t['status'] = 'error'
            t['error'] = 'yt-dlp no encontrado - ejecuta: uv tool install yt-dlp'


def _render_status(job: dict) -> str:
    items = []
    for t in job['tracks']:
        url_short = (t['url'][:70] + '...') if len(t['url']) > 70 else t['url']
        s = t['status']

        if s == 'pending':
            items.append(
                f'<li class="tr tr-pending">'
                f'<div class="tr-head"><span class="tr-label">en cola</span></div>'
                f'<span class="tr-url">{url_short}</span></li>'
            )
        elif s == 'running':
            items.append(
                f'<li class="tr tr-running">'
                f'<div class="tr-head"><span class="tr-label">descargando...</span></div>'
                f'<span class="tr-url">{url_short}</span></li>'
            )
        elif s == 'analyzing':
            track_count = t.get('track_count', 1)
            count_txt = f'{track_count} tracks' if track_count > 1 else '1 track'
            items.append(
                f'<li class="tr tr-analyzing">'
                f'<div class="tr-head">'
                f'<span class="tr-label">analizando BPM...</span>'
                f'<span class="bpm-chip bpm-pending">{count_txt}</span>'
                f'</div>'
                f'<span class="tr-url">{url_short}</span></li>'
            )
        elif s == 'done':
            if 'bpm' in t:
                bpm_html = f'<span class="bpm-chip">{int(t["bpm"])} BPM</span>'
            elif 'bpm_avg' in t:
                bpm_html = (
                    f'<span class="bpm-chip">'
                    f'{t["bpm_count"]} tracks &middot; avg {int(t["bpm_avg"])} BPM'
                    f'</span>'
                )
            else:
                bpm_html = ''
            items.append(
                f'<li class="tr tr-done">'
                f'<div class="tr-head">'
                f'<span class="tr-label">listo</span>'
                f'{bpm_html}'
                f'</div>'
                f'<span class="tr-url">{url_short}</span></li>'
            )
        else:
            items.append(
                f'<li class="tr tr-error">'
                f'<div class="tr-head"><span class="tr-label">error</span></div>'
                f'<span class="tr-url">{url_short}</span>'
                f'<span class="tr-err">{t["error"]}</span></li>'
            )
    return (
        '<div class="status-box">'
        '<p class="status-head">Cola de descargas &mdash; Música/DiscoDownload</p>'
        f'<ul class="tr-list">{"".join(items)}</ul>'
        '</div>'
    )


HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{{AUTO_REFRESH}}
<title>DISCO DOWNLOAD</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Monoton&family=Righteous&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --pink:#FF006E;
  --purple:#7B2FBE;
  --gold:#FFD700;
  --gold-dark:#7A5F00;
  --crimson:#8B0000;
  --silver:#C0C0C0;
  --lavender:#c084fc;
  --bg:#08000F;
  --text:#FFF5E0;
}

body{
  min-height:100vh;background:var(--bg);color:var(--text);
  font-family:'Righteous',cursive;overflow-x:hidden;
  animation:bgpulse 10s ease-in-out infinite alternate;
}
@keyframes bgpulse{
  0%  {background-color:#08000F}
  50% {background-color:#0D0018}
  100%{background-color:#0F0008}
}

.orb{position:fixed;border-radius:50%;pointer-events:none;filter:blur(90px);opacity:.07;animation:drift 22s ease-in-out infinite}
.orb-a{width:480px;height:480px;background:var(--purple);top:-160px;left:-160px;animation-duration:22s}
.orb-b{width:360px;height:360px;background:var(--crimson);bottom:-100px;right:-100px;animation-duration:30s;animation-delay:-11s}
.orb-c{width:290px;height:290px;background:var(--pink);top:42%;left:52%;animation-duration:34s;animation-delay:-17s}
@keyframes drift{
  0%,100%{transform:translate(0,0) scale(1)}
  33%    {transform:translate(50px,40px) scale(1.1)}
  66%    {transform:translate(-35px,55px) scale(.93)}
}

.scene{position:relative;height:210px;display:flex;justify-content:center;overflow:hidden}

.rays{
  position:absolute;width:560px;height:560px;top:calc(116px - 280px);left:50%;transform:translateX(-50%);
  border-radius:50%;
  background:conic-gradient(
    from 0deg,
    transparent 0deg 9deg,rgba(255,215,0,.22) 9deg 12deg,
    transparent 12deg 29deg,rgba(255,0,110,.17) 29deg 32deg,
    transparent 32deg 49deg,rgba(180,100,255,.19) 49deg 52deg,
    transparent 52deg 69deg,rgba(255,215,0,.15) 69deg 72deg,
    transparent 72deg 100deg,rgba(0,220,255,.16) 100deg 103deg,
    transparent 103deg 130deg,rgba(255,0,110,.13) 130deg 133deg,
    transparent 133deg 160deg,rgba(255,215,0,.18) 160deg 163deg,
    transparent 163deg 190deg,rgba(180,100,255,.14) 190deg 193deg,
    transparent 193deg 220deg,rgba(0,220,255,.12) 220deg 223deg,
    transparent 223deg 250deg,rgba(255,215,0,.16) 250deg 253deg,
    transparent 253deg 280deg,rgba(255,0,110,.13) 280deg 283deg,
    transparent 283deg 310deg,rgba(180,100,255,.15) 310deg 313deg,
    transparent 313deg 340deg,rgba(0,220,255,.10) 340deg 343deg,
    transparent 343deg 360deg
  );
  animation:rayspin 14s linear infinite;z-index:0;
}
@keyframes rayspin{to{transform:translateX(-50%) rotate(360deg)}}

.ball-wrap{position:absolute;top:0;display:flex;flex-direction:column;align-items:center;z-index:1}
.string{width:2px;height:50px;background:linear-gradient(to bottom,rgba(150,150,150,.3),rgba(210,210,210,.85))}

.ball{
  width:132px;height:132px;border-radius:50%;position:relative;overflow:hidden;
  background:
    repeating-linear-gradient(0deg,transparent,transparent 10px,rgba(0,0,0,.55) 10px,rgba(0,0,0,.55) 12px),
    repeating-linear-gradient(90deg,transparent,transparent 10px,rgba(0,0,0,.55) 10px,rgba(0,0,0,.55) 12px),
    radial-gradient(ellipse at 36% 28%,#fff 0%,#d8d8d8 14%,#a0a0a0 32%,#606060 52%,#282828 72%,#0a0a0a 100%);
  box-shadow:
    0 0 0 2px rgba(200,200,200,.15),
    0 0 24px rgba(255,215,0,.95),0 0 58px rgba(255,0,110,.6),0 0 100px rgba(123,47,190,.45),
    inset 0 0 28px rgba(0,0,0,.8);
  animation:ballscroll 1.5s linear infinite,ballglow 2.5s ease-in-out infinite alternate;
}
.ball::before{
  content:'';position:absolute;inset:0;border-radius:50%;
  background:
    radial-gradient(ellipse 26px 13px at 27% 27%,rgba(255,215,0,.95),transparent 85%),
    radial-gradient(ellipse 18px 11px at 58% 20%,rgba(255,0,110,.88),transparent 85%),
    radial-gradient(ellipse 16px 11px at 73% 55%,rgba(0,230,255,.78),transparent 85%),
    radial-gradient(ellipse 22px 11px at 40% 67%,rgba(180,100,255,.88),transparent 85%),
    radial-gradient(ellipse 14px  9px at 17% 68%,rgba(255,215,0,.78),transparent 85%);
}
.ball::after{
  content:'';position:absolute;inset:0;border-radius:50%;
  background:radial-gradient(ellipse 52% 36% at 33% 24%,rgba(255,255,255,.58),transparent 68%);
}
@keyframes ballscroll{
  from{background-position:0 0,0 0,0 0}
  to  {background-position:0 0,12px 0,0 0}
}
@keyframes ballglow{
  0%  {box-shadow:0 0 22px rgba(255,215,0,.8),0 0 52px rgba(255,0,110,.5),0 0 94px rgba(123,47,190,.38),inset 0 0 28px rgba(0,0,0,.8)}
  100%{box-shadow:0 0 34px rgba(255,215,0,1),0 0 78px rgba(255,0,110,.75),0 0 136px rgba(123,47,190,.6),inset 0 0 28px rgba(0,0,0,.8)}
}

main{
  position:relative;max-width:620px;margin:0 auto 70px;padding:44px 40px 48px;
  background:linear-gradient(148deg,rgba(139,0,0,.12),rgba(123,47,190,.09)),rgba(16,0,26,.9);
  border:1px solid rgba(255,215,0,.28);
  box-shadow:0 0 0 1px rgba(255,0,110,.1),0 0 55px rgba(123,47,190,.28),0 14px 80px rgba(0,0,0,.9);
}

.cr{position:absolute;width:52px;height:52px;border-color:var(--gold);border-style:solid}
.cr.tl{top:14px;left:14px;border-width:2px 0 0 2px}
.cr.tr{top:14px;right:14px;border-width:2px 2px 0 0}
.cr.bl{bottom:14px;left:14px;border-width:0 0 2px 2px}
.cr.br{bottom:14px;right:14px;border-width:0 2px 2px 0}
.cr::after{content:'';position:absolute;width:30px;height:30px;border-color:rgba(255,215,0,.36);border-style:solid}
.cr.tl::after{top:7px;left:7px;border-width:1px 0 0 1px}
.cr.tr::after{top:7px;right:7px;border-width:1px 1px 0 0}
.cr.bl::after{bottom:7px;left:7px;border-width:0 0 1px 1px}
.cr.br::after{bottom:7px;right:7px;border-width:0 1px 1px 0}

header{text-align:center;margin-bottom:32px}
h1{
  font-family:'Monoton',cursive;font-size:clamp(2rem,7vw,3.2rem);letter-spacing:.06em;line-height:1.22;
  background:linear-gradient(128deg,#FFD700 0%,#FF99CC 32%,#FFD700 58%,rgba(255,255,255,.8) 88%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 12px rgba(255,215,0,.65)) drop-shadow(0 0 26px rgba(255,0,110,.45));
  animation:hglow 4s ease-in-out infinite alternate;
}
@keyframes hglow{
  0%  {filter:drop-shadow(0 0 8px rgba(255,215,0,.5)) drop-shadow(0 0 18px rgba(255,0,110,.35))}
  100%{filter:drop-shadow(0 0 22px rgba(255,215,0,1)) drop-shadow(0 0 44px rgba(255,0,110,.72))}
}
.tagline{margin-top:11px;font-size:.78rem;letter-spacing:.3em;text-transform:uppercase;color:var(--silver);text-shadow:0 0 10px rgba(192,192,192,.5)}
.rule{margin:0 0 24px;border:none;height:1px;background:linear-gradient(90deg,transparent,var(--gold) 20%,var(--pink) 50%,var(--gold) 80%,transparent);opacity:.45}

.booth{display:flex;flex-direction:column;gap:16px}
.lbl{display:block;font-size:.78rem;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);text-shadow:0 0 8px rgba(255,215,0,.45);margin-bottom:4px}

textarea[name="urls"]{
  width:100%;background:rgba(8,0,15,.92);border:1px solid rgba(255,215,0,.38);border-radius:2px;
  color:#fff;font-family:'Courier New',monospace;font-size:.87rem;line-height:1.65;
  padding:14px 16px;resize:vertical;outline:none;transition:border-color .22s,box-shadow .22s;
}
textarea[name="urls"]::placeholder{color:rgba(255,215,0,.28);font-style:italic}
textarea[name="urls"]:focus{border-color:var(--pink);box-shadow:0 0 0 2px rgba(255,0,110,.22),0 0 24px rgba(255,0,110,.12)}

.fmt-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}

select[name="fmt"]{
  background:rgba(8,0,15,.94);border:1px solid rgba(255,215,0,.5);border-radius:2px;
  color:var(--gold);font-family:'Righteous',cursive;font-size:.95rem;
  padding:11px 36px 11px 14px;cursor:pointer;outline:none;
  appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23FFD700' stroke-width='2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 11px center;transition:border-color .2s,box-shadow .2s;
}
select[name="fmt"]:focus{border-color:var(--pink);box-shadow:0 0 14px rgba(255,0,110,.3)}

button[type="submit"]{
  flex:1;min-width:165px;padding:14px 26px;font-family:'Monoton',cursive;font-size:.82rem;letter-spacing:.1em;
  color:#0a0000;cursor:pointer;border:none;border-radius:2px;outline:none;
  background:linear-gradient(135deg,#FFD700 0%,#FFFAAA 20%,#FFD700 40%,#C8A200 60%,#FFD700 76%,#FFFDE0 100%);
  box-shadow:0 5px 0 var(--gold-dark),0 7px 20px rgba(0,0,0,.7),0 0 24px rgba(255,215,0,.6),inset 0 1px 0 rgba(255,255,255,.8),inset 0 -2px 0 rgba(0,0,0,.22);
  transform:translateY(0);transition:transform .12s,box-shadow .18s,filter .2s;
}
button[type="submit"]:hover{
  filter:brightness(1.1) saturate(1.3);transform:translateY(-3px);
  box-shadow:0 8px 0 var(--gold-dark),0 10px 32px rgba(0,0,0,.55),0 0 42px rgba(255,215,0,.9),0 0 72px rgba(255,0,110,.45),inset 0 1px 0 rgba(255,255,255,.85),inset 0 -2px 0 rgba(0,0,0,.15);
}
button[type="submit"]:active{
  transform:translateY(4px);
  box-shadow:0 1px 0 var(--gold-dark),0 2px 10px rgba(0,0,0,.7),0 0 16px rgba(255,215,0,.45),inset 0 3px 5px rgba(0,0,0,.35);
}
button[type="submit"]:focus-visible{outline:2px solid var(--pink);outline-offset:3px}

.chk-label{
  display:flex;align-items:center;gap:9px;cursor:pointer;
  font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;color:var(--silver);
  white-space:nowrap;
}
.chk-label input{
  appearance:none;-webkit-appearance:none;
  width:16px;height:16px;flex-shrink:0;
  border:1px solid rgba(255,215,0,.5);border-radius:2px;
  background:rgba(8,0,15,.92);cursor:pointer;position:relative;
  transition:background .15s,border-color .15s;
}
.chk-label input:checked{background:var(--gold);border-color:var(--gold)}
.chk-label input:checked::after{
  content:'';position:absolute;left:4px;top:1px;
  width:5px;height:9px;
  border:2px solid #000;border-top:none;border-left:none;
  transform:rotate(45deg);
}
.chk-label input:focus-visible{outline:2px solid var(--pink);outline-offset:2px}

/* ── Download status block ─────────────────────────────── */
.status-box{
  margin-top:26px;
  border:1px solid rgba(255,215,0,.35);
  background:linear-gradient(148deg,rgba(139,0,0,.15),rgba(123,47,190,.1));
}
.status-head{
  padding:10px 16px;
  font-size:.72rem;letter-spacing:.25em;text-transform:uppercase;
  color:var(--gold);text-shadow:0 0 8px rgba(255,215,0,.4);
  border-bottom:1px solid rgba(255,215,0,.2);
}
.tr-list{list-style:none;padding:6px 0}
.tr{
  display:flex;flex-direction:column;gap:3px;
  padding:9px 16px;border-bottom:1px solid rgba(255,255,255,.04);
  font-family:'Courier New',monospace;font-size:.82rem;
}
.tr:last-child{border-bottom:none}

/* label + bpm chip on one line */
.tr-head{display:flex;justify-content:space-between;align-items:center;gap:8px}

.tr-label{font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;opacity:.65;flex-shrink:0}
.tr-url{opacity:.8;word-break:break-all;line-height:1.4}
.tr-err{font-size:.78rem;color:var(--pink);opacity:.9;margin-top:1px}

/* ── BPM chip ── */
.bpm-chip{
  font-family:'Courier New',monospace;font-size:.72rem;letter-spacing:.14em;
  color:var(--gold);background:rgba(255,215,0,.07);
  border:1px solid rgba(255,215,0,.32);border-radius:2px;
  padding:2px 8px;white-space:nowrap;flex-shrink:0;
  text-shadow:0 0 8px rgba(255,215,0,.45);
}
/* analyzing variant — purple tones, pulsing */
.bpm-chip.bpm-pending{
  color:var(--lavender);
  background:rgba(192,132,252,.07);
  border-color:rgba(192,132,252,.28);
  text-shadow:0 0 8px rgba(192,132,252,.4);
  animation:chipulse .9s ease-in-out infinite alternate;
}
@keyframes chipulse{0%{opacity:.55}100%{opacity:1}}

/* ── Row state colours ── */
.tr-pending  {color:var(--silver);opacity:.55}
.tr-running  {color:var(--gold);animation:trpulse 1.1s ease-in-out infinite alternate}
.tr-analyzing{color:var(--lavender)}
.tr-analyzing .tr-label{animation:trpulse 1.1s ease-in-out infinite alternate}
.tr-done     {color:#00e5a0}
.tr-error    {color:var(--pink)}

@keyframes trpulse{0%{opacity:.65}100%{opacity:1}}

.msg{
  margin-top:24px;padding:16px 20px;
  background:linear-gradient(135deg,rgba(139,0,0,.3),rgba(123,47,190,.2));
  border:1px solid rgba(255,215,0,.5);border-left:4px solid var(--gold);
  color:var(--gold);font-size:.9rem;letter-spacing:.08em;line-height:1.5;
  text-shadow:0 0 10px rgba(255,215,0,.6);animation:msgpop .42s cubic-bezier(.34,1.56,.64,1);
}
@keyframes msgpop{0%{opacity:0;transform:scale(.95) translateY(8px)}100%{opacity:1;transform:scale(1) translateY(0)}}

.stars{text-align:center;margin-top:28px;color:rgba(255,215,0,.3);letter-spacing:.7em}

@media(max-width:520px){
  main{margin:0 10px 50px;padding:32px 20px 38px}
  .fmt-row{flex-direction:column;align-items:stretch}
  button[type="submit"]{text-align:center}
  .cr{width:36px;height:36px}.cr::after{width:20px;height:20px}
  h1{font-size:clamp(1.7rem,9vw,2.4rem)}
}
@media(prefers-reduced-motion:reduce){
  .rays,.ball,.orb,body,h1,.tr-running,.tr-analyzing,.bpm-chip.bpm-pending{animation:none!important}
  .ball{background-position:0 0,0 0,0 0}
}
</style>
</head>
<body>

<div class="orb orb-a"></div>
<div class="orb orb-b"></div>
<div class="orb orb-c"></div>

<div class="scene">
  <div class="rays"></div>
  <div class="ball-wrap">
    <div class="string"></div>
    <div class="ball"></div>
  </div>
</div>

<main>
  <div class="cr tl"></div><div class="cr tr"></div>
  <div class="cr bl"></div><div class="cr br"></div>

  <header>
    <h1>DISCO<br>DOWNLOAD</h1>
    <p class="tagline">La Máquina Extractora de Sonido del Studio 54</p>
  </header>

  <hr class="rule">

  {{FFMPEG_WARN}}

  <form method="post" class="booth">
    <div>
      <label class="lbl" for="urls">Suelta tus enlaces, cielo</label>
      <textarea name="urls" id="urls" rows="6"
        placeholder="https://youtube.com/watch?v=...&#10;Un enlace por línea, guapi"></textarea>
    </div>
    <div class="fmt-row">
      <label class="lbl" for="fmt" style="margin:0">Formato</label>
      <select name="fmt" id="fmt">
        <option>mp3</option>
        <option>wav</option>
      </select>
      <label class="chk-label">
        <input type="checkbox" name="playlist" id="playlist">
        Playlist completa
      </label>
      <button type="submit">A BAILAR</button>
    </div>
  </form>

  {{STATUS_BLOCK}}

  <p class="stars">* * * * *</p>
</main>

<script>
(function(){
  var ta  = document.getElementById('urls');
  var sel = document.getElementById('fmt');
  var chk = document.getElementById('playlist');

  // Clear saved URLs when arriving on a status page (downloads were queued)
  if (window.location.search.indexOf('run=') !== -1) {
    localStorage.removeItem('dd_urls');
  } else {
    var sv = localStorage.getItem('dd_urls');
    if (sv) ta.value = sv;
  }

  var sf = localStorage.getItem('dd_fmt');
  if (sf) sel.value = sf;

  var sp = localStorage.getItem('dd_playlist');
  if (sp) chk.checked = sp === '1';

  ta.addEventListener('input',   function(){ localStorage.setItem('dd_urls',     ta.value); });
  sel.addEventListener('change', function(){ localStorage.setItem('dd_fmt',      sel.value); });
  chk.addEventListener('change', function(){ localStorage.setItem('dd_playlist', chk.checked ? '1' : '0'); });
})();
</script>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        urls          = [u.strip() for u in request.form['urls'].splitlines() if u.strip()]
        fmt           = request.form['fmt']
        full_playlist = request.form.get('playlist') == 'on'
        if urls:
            run_id = uuid.uuid4().hex[:8]
            tracks = [{'url': u, 'status': 'pending', 'error': ''} for u in urls]
            with _lock:
                _jobs[run_id] = {'tracks': tracks, 'fmt': fmt}
            for i, u in enumerate(urls):
                threading.Thread(
                    target=_download, args=(run_id, i, u, fmt, full_playlist), daemon=True
                ).start()
            return redirect(f'/?run={run_id}')

    run_id = request.args.get('run', '')
    job    = None
    if run_id:
        with _lock:
            raw = _jobs.get(run_id)
            if raw:
                job = {'tracks': [dict(t) for t in raw['tracks']], 'fmt': raw['fmt']}

    still_running = job and any(
        t['status'] in ('pending', 'running', 'analyzing') for t in job['tracks']
    )
    auto_refresh  = '<meta http-equiv="refresh" content="2">' if still_running else ''
    status_block  = _render_status(job) if job else ''

    return (HTML
            .replace('{{AUTO_REFRESH}}',  auto_refresh)
            .replace('{{FFMPEG_WARN}}',   _FFMPEG_WARN if not FFMPEG_OK else '')
            .replace('{{STATUS_BLOCK}}',  status_block))


if __name__ == '__main__':
    app.run(port=5555)
