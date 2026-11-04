import io

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _upload(client, headers, data, name):
    return client.post("/api/documents", headers=headers, content_type="multipart/form-data",
                       data={"file": (io.BytesIO(data), name), "document_type": "aadhaar"})


def test_upload_download_and_privacy(client, student_headers, other_headers):
    r = _upload(client, student_headers, PNG, "id.png")
    assert r.status_code == 201
    doc_id = r.get_json()["data"]["id"]
    assert client.get(f"/api/documents/{doc_id}/download", headers=student_headers).status_code == 200
    assert client.get(f"/api/documents/{doc_id}/download", headers=other_headers).status_code == 404
    assert client.get(f"/api/documents/{doc_id}/download").status_code == 401


def test_rejects_bad_extension_and_spoofed_content(client, student_headers):
    assert _upload(client, student_headers, b"MZ...", "evil.exe").status_code == 415
    assert _upload(client, student_headers, b"not a pdf at all", "fake.pdf").status_code == 415
    assert _upload(client, student_headers, PNG, "../../etc/x.png").status_code == 201
