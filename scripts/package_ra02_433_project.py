"""Bundle one solved AEDT project with its matching results folder and hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def package(project,archive):
    results=project.with_suffix(".aedtresults")
    if not project.is_file() or not results.is_dir(): raise ValueError("Need .aedt and matching .aedtresults")
    files=[project]+sorted(p for p in results.rglob("*") if p.is_file())
    manifest=[{"path":p.relative_to(project.parent).as_posix(),"bytes":p.stat().st_size,
               "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    archive.parent.mkdir(parents=True,exist_ok=True)
    manifest_path=archive.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(project.parent).as_posix())
        z.write(manifest_path,"manifest.json")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise RuntimeError("Archive integrity failed")
    print(json.dumps({"archive":str(archive),"files":len(files),"bytes":archive.stat().st_size,"integrity":"PASS"}))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("project",type=Path);p.add_argument("archive",type=Path)
    args=p.parse_args();package(args.project,args.archive)
