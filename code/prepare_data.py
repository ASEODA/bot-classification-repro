"""고정 릴리스에서 원문 코퍼스와 파서 모델을 준비한다."""
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


def public_openrouter(data):
    """측정값은 보존하고, 배포에 필요 없는 실행·판정 기록과 로컬 정보는 정리한다."""
    settings = data["설정"]
    for key in ("실행", "smoke", "시험입력", "관문통과", "사전선언",
                "구현결정", "관문", "속도", "소요"):
        settings.pop(key, None)
    settings["methods"] = "data/records/openrouter.md"
    pipeline = settings["파이프라인"]
    pipeline["모델경로"] = {k: v.split("/resources/")[-1]
                            for k, v in pipeline["모델경로"].items()}
    settings["정제규칙"].pop("출처", None)
    if "모델ID표" in settings:
        for key in ("미정_표기", "결정", "비고"):
            settings["모델ID표"].pop(key, None)
        settings["시각규칙"]["출처"] = "BotSim: reddit_agent.py, comment_time_function"
        settings["라벨"] = "생성 계정의 라벨은 봇이며, 기준 계정은 원본 라벨을 따른다."
        settings["복사"]["규칙"] = (
            "소문자화하고 단어 문자·공백 이외의 문자를 제거한 뒤 공백을 합친다. "
            "동일 원문 또는 SequenceMatcher 유사도 >= 0.9를 제외하며, 민감도 분석에는 >= 0.8을 사용한다. "
            "길이 차이가 긴 원문의 0.30을 넘으면 비교 없이 0.8 미만으로 분류한다. "
            "정규화 결과가 모두 빈 문자열이면 동일 원문으로 본다. 계정 및 대응 부분집합에 제외 규칙을 적용한다."
        )
        for variants in (settings["변형_이름표"], settings["복사"]["변형_이름표"]):
            variants.update({
                "계정": "주 분석: 동일 원문 또는 유사도 >= 0.9를 제외한다.",
                "복사민감도": "민감도 분석: 유사도 >= 0.8을 제외한다.",
                "복사제외없음": "복사에 따른 제외 없이 비교한다.",
            })
    else:
        settings["집단정의"] = {
            "사람": "댓글 한정 적격 사람 계정의 comment_1·comment_2.",
            "원봇": "페르소나 원본 계정 509개가 후보이며, comment_1에서 복사 슬롯을 제외한다.",
            "완전모방기": "MIM_ 접두사를 사용하는 완전모방기 대조군 계정.",
        }
        settings["봉인"] = "분류기 시험용 사람 234개 계정을 봉인 표시하고 고정 분류기 평가용으로 남겨둔다."
        settings["라벨"] = "원본 사람 계정은 사람, 원봇·완전모방기 대조군은 봇으로 표시한다."
    input_names = {
        "원본JSON": "botsim_documents", "Users.csv": "botsim_users",
        "01_py": "botsim_screening_code", "02_기능어": "function_word_list",
        "09-2_JSON": "comment_only_accounts", "분할.json": "split_configuration",
        "프롬프트대장.jsonl": "prompt_records", "준비_요약.json": "preparation_summary",
        "완전모방기_문서.jsonl": "example_texts", "12-0_py": "fox8_extraction_code",
        "12-0_JSON": "fox8_measurements", "fox8_sqlite": "fox8_database",
        "13-0_계정사전.json": "control_measurements", "모델ID표.json": "generation_models",
    }
    settings["입력"] = {input_names.get(k, k): v["sha256"] if isinstance(v, dict) else v
                        for k, v in settings["입력"].items()}
    return data


def gzip_openrouter(src, path):
    data = public_openrouter(json.load(src))
    payload = (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    gzip_copy(io.BytesIO(payload), path)


def prepare_models(archive, path):
    """모델 파일은 보존하고 압축 헤더의 로컬 정보와 비결정적 값을 제거한다."""
    with tarfile.open(archive) as src, path.open("wb") as out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as dst:
                for member in sorted(src.getmembers(), key=lambda m: m.name):
                    if member.isfile():
                        info = tarfile.TarInfo(member.name)
                        info.size, info.mode = member.size, 0o644
                        with src.extractfile(member) as f:
                            dst.addfile(info, f)


def convert(archive, dest):
    """원본 압축파일에서 필요한 입력만 직접 읽는다."""
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
                if filename.endswith(".json"):
                    gzip_openrouter(src, dest / target)
                else:
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
    if not URL.startswith("https://github.com/"):
        raise RuntimeError("익명 배포본에서는 원자료를 내려받을 수 없습니다. "
                           "기본 fast 모드(bash run.sh)로 재현하세요.")
    print("원자료·모델 준비: 고정 릴리스에서 약 354 MB 다운로드", flush=True)
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
        prepare_models(work / "models-20260927.tar.gz", prepared / "stanza-models.tar.gz")
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
