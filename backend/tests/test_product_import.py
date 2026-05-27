from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import StockLedgerEntry, StockReservation, WarehouseStock
from app.models.master_data import Product


def register_and_login(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post("/api/auth/register", json={"company_name": "Acme", "name": "Admin", "email": email, "password": "StrongPass123!"})
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def csv_file(content: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("products.csv", content.encode("utf-8"), "text/csv")}


def xlsx_file() -> dict[str, tuple[str, bytes, str]]:
    shared = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="6" uniqueCount="6">
  <si><t>Product Name</t></si>
  <si><t>Item Code</t></si>
  <si><t>unit</t></si>
  <si><t>XLSX Widget</t></si>
  <si><t>XLSX-1</t></si>
  <si><t>pcs</t></si>
</sst>"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>"""
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c></row><row r="2"><c r="A2" t="s"><v>3</v></c><c r="B2" t="s"><v>4</v></c><c r="C2" t="s"><v>5</v></c></row></sheetData></worksheet>"""
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
      archive.writestr("[Content_Types].xml", content_types)
      archive.writestr("_rels/.rels", root_rels)
      archive.writestr("xl/workbook.xml", workbook)
      archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
      archive.writestr("xl/sharedStrings.xml", shared)
      archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return {"file": ("products.xlsx", stream.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


def upload(client: TestClient, token: str, content: str, mode: str = "create_only", create_missing: bool = False):
    return client.post(
        "/api/imports/products/upload",
        data={"mode": mode, "create_missing_references": str(create_missing).lower()},
        files=csv_file(content),
        headers=auth_headers(token),
    )


VALID_CSV = "name,sku,unit,barcode,cost_price,selling_price,reorder_level,track_batch,track_expiry,track_serial\nWidget,W-1,pcs,111,10,12,5,false,false,false\n"


def test_upload_valid_csv_and_preview_does_not_commit(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    response = upload(client, login["access_token"], VALID_CSV)
    validate = client.post(f"/api/imports/products/{response.json()['job']['id']}/validate", json={}, headers=auth_headers(login["access_token"]))

    assert response.status_code == 200
    assert validate.status_code == 200
    assert validate.json()["job"]["valid_rows"] == 1
    assert db_session.query(Product).count() == 0


def test_upload_invalid_csv_missing_required_column(client: TestClient) -> None:
    login = register_and_login(client)

    response = upload(client, login["access_token"], "name,unit\nWidget,pcs\n")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMPORT_COLUMNS"


def test_upload_invalid_utf8_file_returns_clean_error(client: TestClient) -> None:
    login = register_and_login(client)

    response = client.post(
        "/api/imports/products/upload",
        data={"mode": "create_only", "create_missing_references": "false"},
        files={"file": ("products.csv", b"\xff\xfe\x00", "text/csv")},
        headers=auth_headers(login["access_token"]),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMPORT_FILE"
    assert "request_id" in response.json()["error"]


def test_duplicate_sku_and_barcode_in_file_are_errors(client: TestClient) -> None:
    login = register_and_login(client)
    content = "name,sku,unit,barcode\nWidget,W-1,pcs,111\nOther,W-1,pcs,111\n"
    job = upload(client, login["access_token"], content).json()["job"]

    validate = client.post(f"/api/imports/products/{job['id']}/validate", json={}, headers=auth_headers(login["access_token"]))

    rows = validate.json()["rows"]
    assert validate.json()["job"]["error_rows"] == 1
    assert rows[1]["status"] == "ERROR"
    assert any("duplicate SKU" in error for error in rows[1]["errors"])
    assert any("duplicate barcode" in error for error in rows[1]["errors"])


def test_existing_sku_blocked_create_only_and_same_sku_other_tenant_allowed(client: TestClient) -> None:
    login_a = register_and_login(client, "a@example.com")
    job_a = upload(client, login_a["access_token"], VALID_CSV).json()["job"]
    client.post(f"/api/imports/products/{job_a['id']}/commit", json={}, headers=auth_headers(login_a["access_token"]))
    second_a = upload(client, login_a["access_token"], VALID_CSV).json()["job"]
    validate_a = client.post(f"/api/imports/products/{second_a['id']}/validate", json={}, headers=auth_headers(login_a["access_token"]))
    login_b = register_and_login(client, "b@example.com")
    job_b = upload(client, login_b["access_token"], VALID_CSV).json()["job"]
    commit_b = client.post(f"/api/imports/products/{job_b['id']}/commit", json={}, headers=auth_headers(login_b["access_token"]))

    assert validate_a.json()["job"]["error_rows"] == 1
    assert commit_b.status_code == 200
    assert commit_b.json()["job"]["created_count"] == 1


def test_existing_barcode_collision_blocked(client: TestClient) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])
    assert client.post("/api/catalog/products", json={"name": "Existing", "sku": "EX-1", "barcode": "111"}, headers=headers).status_code == 201
    job = upload(client, login["access_token"], "name,sku,unit,barcode\nWidget,W-1,pcs,111\n").json()["job"]

    validate = client.post(f"/api/imports/products/{job['id']}/validate", json={}, headers=headers)

    assert validate.json()["job"]["error_rows"] == 1
    assert any("barcode already exists" in error for error in validate.json()["rows"][0]["errors"])


def test_commit_creates_products_skips_invalid_and_does_not_mutate_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    content = "name,sku,unit,barcode\nWidget,W-1,pcs,111\nBroken,,pcs,222\n"
    job = upload(client, login["access_token"], content).json()["job"]

    commit = client.post(f"/api/imports/products/{job['id']}/commit", json={}, headers=auth_headers(login["access_token"]))

    assert commit.status_code == 200
    assert commit.json()["job"]["created_count"] == 1
    assert commit.json()["job"]["skipped_count"] == 1
    assert db_session.query(Product).count() == 1
    assert db_session.query(WarehouseStock).count() == 0
    assert db_session.query(StockLedgerEntry).count() == 0
    assert db_session.query(StockReservation).count() == 0


def test_update_existing_and_upsert_modes(client: TestClient) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])
    assert client.post("/api/catalog/products", json={"name": "Old", "sku": "W-1", "unit": "pcs"}, headers=headers).status_code == 201
    update_job = upload(client, login["access_token"], "name,sku,unit\nNew,W-1,box\n", "update_existing").json()["job"]
    update = client.post(f"/api/imports/products/{update_job['id']}/commit", json={}, headers=headers)
    upsert_job = upload(client, login["access_token"], "name,sku,unit\nOther,W-2,pcs\n", "upsert").json()["job"]
    upsert = client.post(f"/api/imports/products/{upsert_job['id']}/commit", json={}, headers=headers)

    products = client.get("/api/catalog/products", headers=headers).json()
    assert update.json()["job"]["updated_count"] == 1
    assert upsert.json()["job"]["created_count"] == 1
    assert {product["sku"] for product in products} == {"W-1", "W-2"}
    assert next(product for product in products if product["sku"] == "W-1")["name"] == "New"


def test_tenant_cannot_access_other_tenant_import_job(client: TestClient) -> None:
    login_a = register_and_login(client, "a@example.com")
    job = upload(client, login_a["access_token"], VALID_CSV).json()["job"]
    login_b = register_and_login(client, "b@example.com")

    response = client.get(f"/api/imports/products/{job['id']}", headers=auth_headers(login_b["access_token"]))

    assert response.status_code == 404


def test_product_search_by_name_sku_and_barcode(client: TestClient) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])
    client.post("/api/catalog/products", json={"name": "Searchable Widget", "sku": "SW-1", "barcode": "BC-1"}, headers=headers)

    by_name = client.get("/api/catalog/products?search=Searchable", headers=headers).json()
    by_sku = client.get("/api/catalog/products?search=SW-1", headers=headers).json()
    by_barcode = client.get("/api/catalog/products?search=BC-1", headers=headers).json()

    assert len(by_name) == 1
    assert len(by_sku) == 1
    assert len(by_barcode) == 1


def test_xlsx_upload_and_column_mapping_work(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client, "xlsx@example.com")
    response = client.post(
        "/api/imports/products/upload",
        data={"mode": "create_only", "create_missing_references": "false"},
        files=xlsx_file(),
        headers=auth_headers(login["access_token"]),
    )
    commit = client.post(f"/api/imports/products/{response.json()['job']['id']}/commit", json={}, headers=auth_headers(login["access_token"]))

    assert response.status_code == 200
    assert commit.status_code == 200
    assert db_session.query(Product).filter(Product.sku == "XLSX-1").count() == 1


def test_products_csv_export_returns_rows(client: TestClient) -> None:
    login = register_and_login(client, "product-export@example.com")
    headers = auth_headers(login["access_token"])
    assert client.post("/api/catalog/products", json={"name": "Export Widget", "sku": "EXPORT-1", "unit": "pcs"}, headers=headers).status_code == 201

    response = client.get("/api/catalog/products/export.csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "EXPORT-1" in response.text
