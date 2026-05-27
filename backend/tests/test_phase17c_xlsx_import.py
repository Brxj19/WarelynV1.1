from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.services.imports import ProductImportService, REQUIRED_FIELDS, OPTIONAL_FIELDS


def _setup(db_session: Session, client: TestClient, email: str = "p17c@example.com"):
    tenant = Tenant(company_name="P17CCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P17CUser", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def test_xlsx_template_download_returns_valid_xlsx(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-dl@example.com")
    resp = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert resp.content[:2] == b"PK"


def test_xlsx_template_has_correct_headers_row(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-hdr@example.com")
    resp = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    content = resp.content
    with ZipFile(BytesIO(content)) as zf:
        all_text = ""
        for name in zf.namelist():
            all_text += zf.read(name).decode("utf-8", errors="ignore")
        for field in REQUIRED_FIELDS:
            assert field in all_text


def test_import_endpoint_accepts_xlsx_file(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-import@example.com")
    xlsx_bytes = ProductImportService.build_template_xlsx()
    # Add a data row to the template
    import csv
    from io import StringIO
    headers = list(REQUIRED_FIELDS) + sorted(OPTIONAL_FIELDS)
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerow({"name": "Test Product", "sku": "TST-001", "unit": "pcs"})
    csv_content = buf.getvalue().encode()
    resp = client.post(
        "/api/imports/products/upload",
        files={"file": ("products.csv", csv_content, "text/csv")},
        data={"mode": "create_only", "create_missing_references": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["job"]["total_rows"] == 1


def test_import_xlsx_produces_same_rows_as_csv(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-same@example.com")
    # Build a minimal XLSX with one data row
    from xml.etree import ElementTree as ET
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    headers = ["name", "sku", "unit"]
    data_row = ["Widget X", "WX-001", "pcs"]

    shared_strings = headers + data_row
    shared_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="{ns}" count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">'
    for s in shared_strings:
        shared_xml += f"<si><t>{s}</t></si>"
    shared_xml += "</sst>"

    sheet_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{ns}"><sheetData>'
    sheet_xml += '<row r="1">'
    for idx in range(len(headers)):
        col = chr(65 + idx)
        sheet_xml += f'<c r="{col}1" t="s"><v>{idx}</v></c>'
    sheet_xml += '</row><row r="2">'
    for idx in range(len(data_row)):
        col = chr(65 + idx)
        sheet_xml += f'<c r="{col}2" t="s"><v>{len(headers) + idx}</v></c>'
    sheet_xml += "</row></sheetData></worksheet>"

    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    workbook_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{ns}" xmlns:r="{rel_ns}"><sheets><sheet name="Products" sheetId="1" r:id="rId1"/></sheets></workbook>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    workbook_rels += '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    workbook_rels += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
    workbook_rels += "</Relationships>"
    rels_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    rels_xml += '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    rels_xml += "</Relationships>"
    ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    content_types = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="{ct_ns}">'
    content_types += '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    content_types += '<Default Extension="xml" ContentType="application/xml"/>'
    content_types += '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    content_types += '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    content_types += '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
    content_types += "</Types>"

    xlsx_buf = BytesIO()
    with ZipFile(xlsx_buf, "w") as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        zf.writestr("xl/sharedStrings.xml", shared_xml)
    xlsx_content = xlsx_buf.getvalue()

    resp = client.post(
        "/api/imports/products/upload",
        files={"file": ("products.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"mode": "create_only", "create_missing_references": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["total_rows"] == 1

    rows_resp = client.get(f"/api/imports/products/{job['id']}/rows", headers={"Authorization": f"Bearer {token}"})
    rows = rows_resp.json()
    assert len(rows) == 1
    assert rows[0]["raw_data"]["name"] == "Widget X"
    assert rows[0]["raw_data"]["sku"] == "WX-001"
