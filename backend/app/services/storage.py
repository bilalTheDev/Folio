import os
import shutil
import zipfile
from pathlib import Path, PurePath

from bson import ObjectId
from fastapi import UploadFile

from app.config import settings
from app.core.errors import AppError

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TXT = "text/plain"
MD = "text/markdown"

ALLOWED_EXTENSIONS = {".pdf": PDF, ".docx": DOCX, ".txt": TXT, ".md": MD}
_READ_CHUNK = 1024 * 1024


def user_dir(user_id: ObjectId | str) -> Path:
    return settings.storage_root / str(user_id)


def files_dir(user_id: ObjectId | str) -> Path:
    return user_dir(user_id) / "files"


def resolve(storage_path: str) -> Path:
    path = (settings.storage_root / storage_path).resolve()
    if settings.storage_root not in path.parents:
        raise AppError(400, "bad_path", "Invalid storage path.")
    return path


def clean_filename(raw: str | None) -> str:
    name = PurePath((raw or "").replace("\\", "/")).name.strip()
    name = "".join(c for c in name if c.isprintable())
    return name[:255] or "untitled"


def _too_large() -> AppError:
    limit_mb = settings.max_upload_bytes // (1024 * 1024)
    return AppError(413, "file_too_large", f"File is larger than the {limit_mb} MB limit.")


def _detect_mime(path: Path, extension: str) -> str:
    """Trust file contents, not the client's Content-Type."""
    with path.open("rb") as fh:
        head = fh.read(8)
    if extension == ".pdf":
        if head.startswith(b"%PDF-"):
            return PDF
    elif extension == ".docx":
        if head.startswith(b"PK\x03\x04") and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                if "word/document.xml" in archive.namelist():
                    return DOCX
    else:
        data = path.read_bytes()
        if b"\x00" not in data:
            try:
                data.decode("utf-8-sig")
                return ALLOWED_EXTENSIONS[extension]
            except UnicodeDecodeError:
                pass
    raise AppError(415, "unsupported_file", f"The file content doesn't match its {extension} extension.")


async def save_upload(upload: UploadFile, user_id: ObjectId, document_id: ObjectId) -> tuple[str, int, str]:
    """Stream the upload to disk, aborting past the size limit. Returns (storage_path, size, mime)."""
    filename = clean_filename(upload.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AppError(415, "unsupported_file", "Upload a PDF, DOCX, TXT, or Markdown file.")

    target_dir = files_dir(user_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{document_id}{extension}"

    size = 0
    try:
        with target.open("wb") as out:
            while chunk := await upload.read(_READ_CHUNK):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise _too_large()
                out.write(chunk)
        if size == 0:
            raise AppError(400, "empty_file", "The file is empty.")
        mime = _detect_mime(target, extension)
    except BaseException:
        target.unlink(missing_ok=True)
        raise

    return target.relative_to(settings.storage_root).as_posix(), size, mime


def delete_file(storage_path: str) -> None:
    try:
        resolve(storage_path).unlink(missing_ok=True)
    except (AppError, OSError):
        pass


def delete_user_tree(user_id: ObjectId | str) -> None:
    path = user_dir(user_id)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def ensure_storage_root() -> None:
    os.makedirs(settings.storage_root, exist_ok=True)
