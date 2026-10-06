from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings


def test_upload_download_and_delete_file(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    upload = client.post(
        f"{settings.API_V1_STR}/files/",
        headers=superuser_token_headers,
        files={"file": ("hello.txt", b"hello template", "text/plain")},
    )
    assert upload.status_code == 201
    asset = upload.json()
    assert asset["original_name"] == "hello.txt"
    assert asset["size"] == len(b"hello template")

    download = client.get(
        f"{settings.API_V1_STR}/files/{asset['id']}",
        headers=superuser_token_headers,
    )
    assert download.status_code == 200
    assert download.content == b"hello template"

    delete = client.delete(
        f"{settings.API_V1_STR}/files/{asset['id']}",
        headers=superuser_token_headers,
    )
    assert delete.status_code == 204
