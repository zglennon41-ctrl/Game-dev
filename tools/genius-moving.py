"""Moving portraits: a few forms of a line as the game moves them (wings, tails, flames, eyes), as one
animated picture for the tree page (docs/genius-lines.md, "What moves").

    python3 tools/genius-moving.py <base> <form id>,<form id>,... OUT.webp [--seconds 2.5] [--fps 15] [--width 1200]

It runs the game's own sheet of those forms with Godot's movie writer (every frame a fixed step of the
game's time, however slow the machine), cuts the row of forms out of each frame, and writes them as one
looping WebP. Needs a display (xvfb-run) and PIL.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTLE = 3.4        # seconds of the game's time before the sheet has measured and laid its forms out


def main():
    args = sys.argv[1:]
    opt = {"--seconds": 2.5, "--fps": 15, "--width": 1200}
    for k in list(opt):
        if k in args:
            i = args.index(k)
            opt[k] = float(args[i + 1])
            del args[i:i + 2]
    base, ids, out = args[0], args[1].split(","), args[2]
    fps = int(opt["--fps"])
    frames = int((SETTLE + opt["--seconds"]) * fps) + 2
    tmp = tempfile.mkdtemp(prefix="moving-")
    try:
        # eight cells across at 1600x900 are 200 pixels each; a row is the top quarter
        cmd = ["godot", "--path", ROOT, "--resolution", "1600x900", "--write-movie", os.path.join(tmp, "f.png"), "--fixed-fps", str(fps),
               "--quit-after", str(frames), "--", "--sheet=" + base, "--only=" + ",".join(ids)]
        if not os.environ.get("DISPLAY"):
            cmd = ["xvfb-run", "-a", "-s", "-screen 0 1600x900x24"] + cmd
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500, check=False)
        files = sorted(glob.glob(os.path.join(tmp, "f*.png")))[int(SETTLE * fps):]
        if len(files) < 4:
            sys.exit("no frames: did the game run?")
        n = min(8, len(ids))
        box = (0, 0, 200 * n, 225)
        w = int(opt["--width"])
        h = int(w * box[3] / box[2])
        ims = [Image.open(f).convert("RGB").crop(box).resize((w, h), Image.LANCZOS) for f in files]
        ims[0].save(out, save_all=True, append_images=ims[1:], duration=int(1000 / fps), loop=0, quality=72, method=4)
        print("%s: %d frames of %d forms, %d KB" % (out, len(ims), n, os.path.getsize(out) // 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
