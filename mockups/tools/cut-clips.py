"""Cut the frames from record-steps.js into one 1920x1080 30 fps MP4 per step (needs ffmpeg on PATH).
usage: python cut-clips.py [rec dir, default ./rec] [out dir, default ../video]"""
import json, os, subprocess, sys, glob

REC = sys.argv[1] if len(sys.argv) > 1 else 'rec'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), '..', 'video')
NAMES = ['r1-1-start', 'r1-2-sign-says-go', 'r1-3-floor-full', 'r1-4-back-to-ramp',
         'r2-1a-camera-count', 'r2-1b-bay-sensors', 'r2-1c-four-circling', 'r2-1d-real-space-0',
         'r2-2-sign-says-up', 'r2-3-p3-fills', 'r2-4-result']

d = json.load(open(os.path.join(REC, 'rec.json'), encoding='utf-8'))
frames, marks = d['frames'], d['marks']
assert len(marks) == len(NAMES) + 1, f'expected {len(NAMES)} steps, got {len(marks) - 1}'
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, '*.mp4')):
    os.remove(f)
# clip k runs from the click that left step k-1 to the end of step k's hold, so the clips join seamlessly
for k, name in enumerate(NAMES, 1):
    a, b = marks[k - 1]['t'], marks[k]['t']
    sel = [f for f in frames if a <= f['t'] <= b]
    lst = os.path.join(REC, f'list{k}.txt')
    with open(lst, 'w') as L:
        for i, f in enumerate(sel):  # screencast frames arrive irregularly: keep each on screen until the next
            nxt = sel[i + 1]['t'] if i + 1 < len(sel) else b
            L.write(f"file '{os.path.abspath(f['file'])}'\nduration {max(0.001, nxt - f['t']):.4f}\n")
        L.write(f"file '{os.path.abspath(sel[-1]['file'])}'\n")
    fn = os.path.join(OUT, f'{k:02d}-{name}.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
                    '-movflags', '+faststart', fn], check=True)
    print(f'{k:02d}-{name}  {b - a:.1f}s')
