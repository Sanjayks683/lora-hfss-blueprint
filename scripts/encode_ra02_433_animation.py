"""Encode native HFSS phase frames; add a caption outside the untouched render."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat


def main(folder):
    paths=sorted((folder/"current_frames").glob("phase_*.jpg"))
    if len(paths)!=36: raise ValueError("Require all 36 native frames, 0-350 degrees in 10-degree steps")
    frames=[]
    try: font=ImageFont.truetype("arial.ttf",22)
    except OSError: font=ImageFont.load_default()
    for i,path in enumerate(paths):
        phase=int(path.stem.split("_")[-1])
        if phase!=i*10: raise ValueError("Incorrect frame order")
        with Image.open(path) as source:
            rgb=source.convert("RGB")
        canvas=Image.new("RGB",(rgb.width,rgb.height+70),"white")
        canvas.paste(rgb,(0,70))
        ImageDraw.Draw(canvas).text((16,12),"HFSS | 433 MHz | Phase %03d deg | 1 W normalization"%phase,fill=(25,45,65),font=font)
        frames.append(canvas)
    palette=frames[0].quantize(colors=256)
    encoded=[frame.quantize(palette=palette) for frame in frames]
    target=folder/"jsurf433_phase.gif"
    encoded[0].save(target,save_all=True,append_images=encoded[1:],duration=100,loop=0,disposal=2,optimize=False)
    with Image.open(target) as result:
        if result.n_frames!=36: raise RuntimeError("GIF did not preserve all frames")
    # Validate visible changes between phases, excluding the added caption.
    with Image.open(paths[0]) as a, Image.open(paths[9]) as b:
        mean_diff=sum(ImageStat.Stat(ImageChops.difference(a.convert("RGB"),b.convert("RGB"))).mean)/3
    if mean_diff<0.1: raise RuntimeError("Native field animation appears static")
    manifest={"frames":36,"phase_step_deg":10,"duration_ms":100,"loop":True,
        "native_render_unchanged":True,"annotation":"Caption added above original HFSS image",
        "phase_0_90_mean_pixel_difference":mean_diff,
        "frame_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (folder/"animation_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"gif":str(target),"frames":36,"phase_0_90_pixel_difference":mean_diff}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path)
    main(parser.parse_args().folder)
