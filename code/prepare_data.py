"""고정된 GitHub Release에서 원자료를 받아 현재 재현본의 입력만 준비한다."""
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://github.com/ASEODA/bot-classification-repro/releases/download/repro-final-20260927/"
ASSETS = {
    "data-final-20260927.tar.gz": "13832d2714e92369e3f457e9eb2cf8abc66403b601c13eac59aa4103e48a9e7a",
    "models-20260927.tar.gz": "ad749895167d692f9273af08fff819b11dfe37727e750365ec20beedab016325",
}


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def gzip_copy(src, path):
    with path.open("wb") as f:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as dst:
            shutil.copyfileobj(src, dst)


def convert(archive, dest):
    """원본 압축파일을 풀지 않고 필요한 입력만 읽는다."""
    with tarfile.open(archive) as tar:
        members = {unicodedata.normalize("NFC", m.name): m for m in tar if m.isfile()}

        def source(suffix):
            matches = [m for name, m in members.items() if name.endswith(suffix)]
            if len(matches) != 1:
                raise ValueError(f"원자료 경로가 하나여야 합니다: {suffix}")
            return tar.extractfile(matches[0])

        archives = {
            "botsim": ("/BotSim-24-Dataset/", {
                "Readme.md": (2026, 8, 12, 21, 4, 50),
                "Users.csv": (2026, 6, 13, 22, 33, 20),
                "user_post_comment.json": (2026, 6, 13, 22, 33, 22),
            }),
            "ud-ewt": ("/02_UD캐시/", {
                "en_ewt-ud-dev.conllu": (2026, 8, 17, 19, 57, 48),
                "en_ewt-ud-test.conllu": (2026, 8, 17, 19, 57, 52),
                "en_ewt-ud-train.conllu": (2026, 8, 17, 19, 57, 48),
            }),
        }
        for name, (prefix, files) in archives.items():
            with zipfile.ZipFile(dest / (name + ".zip"), "w") as z:
                for filename, date in files.items():
                    info = zipfile.ZipInfo(name + "/" + filename, date)
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    with source(prefix + filename) as src:
                        z.writestr(info, src.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

        with source("/fox8_23_dataset.ndjson.gz") as src, (dest / "fox8.ndjson.gz").open("wb") as dst:
            shutil.copyfileobj(src, dst)
        for filename, target in {
            "12-1_계정사전.json": "openrouter-counts.json.gz",
            "13-0_계정사전.json": "openrouter-controls.json.gz",
            "완전모방기_문서.jsonl": "openrouter-human-examples.jsonl.gz",
        }.items():
            with source("/12_OpenRouter/" + filename) as src:
                gzip_copy(src, dest / target)

        calls = sorted((m for name, m in members.items()
                        if "/12_OpenRouter/호출기록_" in name and name.endswith(".jsonl")),
                       key=lambda m: Path(m.name).name)
        if len(calls) != 5:
            raise ValueError("OpenRouter 원자료는 5모델이어야 합니다.")
        with (dest / "openrouter.jsonl.gz").open("wb") as f:
            with gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
                for member in calls:
                    with io.TextIOWrapper(tar.extractfile(member), encoding="utf-8") as src:
                        for ln, line in enumerate(src, 1):
                            row = json.loads(line)
                            if row.get("종류") != "슬롯":
                                continue
                            selected = {
                                "source_file": Path(member.name).name, "source_line": ln,
                                "slot_id": row.get("슬롯id"), "model": row.get("요청모델"),
                                "status": row.get("상태"), "post_id": row.get("게시물id"),
                                "post_time": row.get("게시물시각"), "comment": row.get("댓글"),
                                "settings_hash": row.get("설정해시"),
                            }
                            gz.write((json.dumps(selected, ensure_ascii=False) + "\n").encode("utf-8"))


def ensure():
    raw = ROOT / "data/raw"
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    expected = {Path(p).name: h for p, h in manifest["files"].items() if p.startswith("data/raw/")}
    if all((raw / name).is_file() for name in expected):
        return
    print("원자료·모델 준비: 고정 GitHub Release에서 약 354 MB 다운로드", flush=True)
    with tempfile.TemporaryDirectory(prefix="bot-repro-data-") as tmp:
        work = Path(tmp)
        for name, sha in ASSETS.items():
            print("다운로드:", name, flush=True)
            request = urllib.request.Request(URL + name, headers={"User-Agent": "bot-classification-repro"})
            with urllib.request.urlopen(request, timeout=120) as src, (work / name).open("wb") as dst:
                shutil.copyfileobj(src, dst)
            if digest(work / name) != sha:
                raise ValueError(f"Release 파일 해시 불일치: {name}")
        prepared = work / "prepared"
        prepared.mkdir()
        convert(work / "data-final-20260927.tar.gz", prepared)
        shutil.copyfile(work / "models-20260927.tar.gz", prepared / "stanza-models.tar.gz")
        for name, sha in expected.items():
            if digest(prepared / name) != sha:
                raise ValueError(f"변환한 원자료 해시 불일치: {name}")
        raw.mkdir(parents=True, exist_ok=True)
        for name in expected:
            if not (raw / name).exists():
                shutil.move(str(prepared / name), raw / name)
    print("원자료 8개 준비 완료. API 호출·재생성 없음.", flush=True)


if __name__ == "__main__":
    ensure()
