"""
video.py — Assemble les 3 slides PNG d'un transfert en un Short vertical MP4.

Effets : leger zoom lent (Ken Burns) sur chaque slide + fondu enchaine entre
les slides. Sortie 1080x1350, ~8 s, sans audio (a ajouter dans l'editeur
YouTube/TikTok au moment de poster).

Necessite FFmpeg installe sur la machine.
    macOS : brew install ffmpeg
"""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path

# Duree d'affichage par slide (secondes) et duree du fondu entre slides
SLIDE_SEC = 2.6
FADE_SEC = 0.5
FPS = 30
W, H = 1080, 1920


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _ken_burns_clip(img: Path, out: Path, dur: float) -> None:
    """Cree un clip video d'une image avec un leger zoom progressif."""
    frames = int(dur * FPS)
    # zoompan : zoom de 1.0 a ~1.06 sur la duree du clip
    vf = (
        f"scale={W*2}:{H*2},"
        f"zoompan=z='min(zoom+0.0009,1.06)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
        f"setsar=1"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(img),
        "-t", f"{dur}", "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(out),
    ]
    subprocess.run(cmd, check=True)


def make_video(slide_paths: list[Path], out_path: Path) -> Path:
    """Assemble les slides (dans l'ordre) en un MP4 avec fondus enchaines."""
    if not ffmpeg_available():
        raise RuntimeError("FFmpeg introuvable. Installe-le : brew install ffmpeg")

    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / "_vtmp"
    tmp.mkdir(exist_ok=True)

    # 1) un clip par slide
    clips = []
    for i, img in enumerate(slide_paths):
        c = tmp / f"clip_{i}.mp4"
        _ken_burns_clip(Path(img), c, SLIDE_SEC)
        clips.append(c)

    # 2) concatenation avec fondu enchaine (xfade) en chaine
    if len(clips) == 1:
        shutil.copy(clips[0], out_path)
    else:
        # construit un filtre xfade progressif
        inputs = []
        for c in clips:
            inputs += ["-i", str(c)]
        # chaine de xfade : clip0 x clip1 x clip2 ...
        filt = ""
        prev = "0:v"
        offset = SLIDE_SEC - FADE_SEC
        for i in range(1, len(clips)):
            out_lbl = f"v{i}"
            filt += (f"[{prev}][{i}:v]xfade=transition=fade:"
                     f"duration={FADE_SEC}:offset={offset:.2f}[{out_lbl}];")
            prev = out_lbl
            offset += SLIDE_SEC - FADE_SEC
        filt = filt.rstrip(";")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
               "-filter_complex", filt, "-map", f"[{prev}]",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
               str(out_path)]
        subprocess.run(cmd, check=True)

    # nettoyage
    for c in clips:
        c.unlink(missing_ok=True)
    try:
        tmp.rmdir()
    except OSError:
        pass
    return out_path


if __name__ == "__main__":
    # test : prend les 3 slides d'un dossier et fait un mp4
    import sys
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out")
    slides = sorted(folder.glob("*_*.png"))
    if slides:
        v = make_video(slides[:3], folder / "test_video.mp4")
        print("video:", v)
    else:
        print("aucune slide trouvee dans", folder)
