import json
from html import escape
from collections import OrderedDict
from decimal import Decimal
from textwrap import wrap
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.exceptions import AppError
from app.models.master_data import Brand, Category, Customer, Product, Vendor, Warehouse, WarehouseLocation
from app.repositories.master_data import (
    BrandRepository,
    CategoryRepository,
    CustomerRepository,
    ProductRepository,
    VendorRepository,
    WarehouseLocationRepository,
    WarehouseRepository,
)
from app.repositories.documents import DocumentsRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.master_data import ProductLabelTrackingMode
from app.services.pdf_service import render_html_to_pdf


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentsRepository(db)
        self.inventory = InventoryRepository(db)
        self.categories = CategoryRepository(db)
        self.brands = BrandRepository(db)
        self.vendors = VendorRepository(db)
        self.customers = CustomerRepository(db)
        self.products = ProductRepository(db)

    def list_categories(self, tenant_id: int) -> list[Category]:
        return self.categories.list_by_tenant(tenant_id)

    def create_category(self, tenant_id: int, values: dict[str, Any]) -> Category:
        return self._commit(self.categories.create_for_tenant(tenant_id, values))

    def update_category(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Category:
        return self._update(self.categories, tenant_id, record_id, values)

    def list_brands(self, tenant_id: int) -> list[Brand]:
        return self.brands.list_by_tenant(tenant_id)

    def create_brand(self, tenant_id: int, values: dict[str, Any]) -> Brand:
        return self._commit(self.brands.create_for_tenant(tenant_id, values))

    def update_brand(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Brand:
        return self._update(self.brands, tenant_id, record_id, values)

    def list_vendors(self, tenant_id: int) -> list[Vendor]:
        return self.vendors.list_by_tenant(tenant_id)

    def create_vendor(self, tenant_id: int, values: dict[str, Any]) -> Vendor:
        return self._commit(self.vendors.create_for_tenant(tenant_id, values))

    def update_vendor(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Vendor:
        return self._update(self.vendors, tenant_id, record_id, values)

    def list_customers(self, tenant_id: int) -> list[Customer]:
        return self.customers.list_by_tenant(tenant_id)

    def create_customer(self, tenant_id: int, values: dict[str, Any]) -> Customer:
        return self._commit(self.customers.create_for_tenant(tenant_id, values))

    def update_customer(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Customer:
        return self._update(self.customers, tenant_id, record_id, values)

    def list_products(self, tenant_id: int, search: str | None = None) -> list[Product]:
        return self.products.list_by_tenant(tenant_id, search)

    def create_product(self, tenant_id: int, values: dict[str, Any]) -> Product:
        self._validate_product_refs(tenant_id, values)
        product = self.products.create_for_tenant(tenant_id, values)
        self.db.flush()
        self._ensure_product_barcode(tenant_id, product)
        return self._commit(product)

    def update_product(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Product:
        self._validate_product_refs(tenant_id, values)
        product = self._update(self.products, tenant_id, record_id, values)
        self._ensure_product_barcode(tenant_id, product)
        return self._commit(product)

    def get_product_detail(self, tenant_id: int, product_id: int) -> dict[str, Any]:
        product = self.products.get_by_id_for_tenant(tenant_id, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        stock_rows = self.inventory.list_stock_for_product(tenant_id, product_id)
        batches = self.inventory.list_batches_for_product(tenant_id, product_id)
        serials = self.inventory.list_serials_for_product(tenant_id, product_id)
        category = self.categories.get_by_id_for_tenant(tenant_id, product.category_id) if product.category_id else None
        brand = self.brands.get_by_id_for_tenant(tenant_id, product.brand_id) if product.brand_id else None
        warehouse_cache: dict[int, str] = {}
        location_cache: dict[int, str] = {}

        def warehouse_name(warehouse_id: int) -> str:
            cached = warehouse_cache.get(warehouse_id)
            if cached is not None:
                return cached
            warehouse = self._warehouse_name(tenant_id, warehouse_id)
            warehouse_cache[warehouse_id] = warehouse
            return warehouse

        def location_name(location_id: int) -> str:
            cached = location_cache.get(location_id)
            if cached is not None:
                return cached
            location = self._location_name(tenant_id, location_id)
            location_cache[location_id] = location
            return location

        stock_rows_data = [
            {
                "warehouse_id": stock.warehouse_id,
                "warehouse_name": warehouse_name(stock.warehouse_id),
                "location_id": stock.location_id,
                "location_name": location_name(stock.location_id),
                "quantity_on_hand": stock.quantity_on_hand,
                "quantity_available": stock.quantity_available,
                "quantity_reserved": stock.quantity_reserved,
            }
            for stock in stock_rows
        ]
        batch_rows_data = []
        for batch in batches:
            batch_payload = self._product_tracking_qr_payload(product, batch=batch)
            batch_rows_data.append(
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "supplier_batch_number": batch.supplier_batch_number,
                    "manufacture_date": batch.manufacture_date,
                    "expiry_date": batch.expiry_date,
                    "warranty_until": batch.warranty_until,
                    "warehouse_id": batch.warehouse_id,
                    "warehouse_name": warehouse_name(batch.warehouse_id),
                    "location_id": batch.location_id,
                    "location_name": location_name(batch.location_id),
                    "quantity_on_hand": batch.quantity_on_hand,
                    "quantity_available": batch.quantity_available,
                    "quantity_reserved": batch.quantity_reserved,
                    "status": batch.status.value if hasattr(batch.status, "value") else str(batch.status),
                    "qr_payload": batch_payload,
                    "qr_matrix": self._qr_matrix(batch_payload),
                }
            )
        serial_rows_data = []
        for serial in serials:
            serial_payload = self._product_tracking_qr_payload(product, serial=serial)
            serial_rows_data.append(
                {
                    "id": serial.id,
                    "serial_number": serial.serial_number,
                    "batch_id": serial.batch_id,
                    "batch_number": self._batch_number_for_serial(serial, batches),
                    "warranty_until": serial.warranty_until,
                    "expires_on": serial.expires_on,
                    "warehouse_id": serial.warehouse_id,
                    "warehouse_name": warehouse_name(serial.warehouse_id),
                    "location_id": serial.location_id,
                    "location_name": location_name(serial.location_id),
                    "status": serial.status.value if hasattr(serial.status, "value") else str(serial.status),
                    "qr_payload": serial_payload,
                    "qr_matrix": self._qr_matrix(serial_payload),
                }
            )
        product_payload = self._product_tracking_qr_payload(product)
        return {
            **self._product_to_dict(product),
            "category_name": category.name if category else None,
            "brand_name": brand.name if brand else None,
            "available_quantity": sum((row.quantity_available or Decimal("0") for row in stock_rows), Decimal("0")),
            "qr_payload": product_payload,
            "qr_matrix": self._qr_matrix(product_payload),
            "stock_rows": stock_rows_data,
            "batches": batch_rows_data,
            "serials": serial_rows_data,
        }

    def _validate_product_refs(self, tenant_id: int, values: dict[str, Any]) -> None:
        if values.get("category_id") and self.categories.get_by_id_for_tenant(tenant_id, values["category_id"]) is None:
            raise AppError("CATEGORY_NOT_FOUND", "Category was not found for this tenant.", 404)
        if values.get("brand_id") and self.brands.get_by_id_for_tenant(tenant_id, values["brand_id"]) is None:
            raise AppError("BRAND_NOT_FOUND", "Brand was not found for this tenant.", 404)

    def _update(self, repository: Any, tenant_id: int, record_id: int, values: dict[str, Any]) -> Any:
        record = repository.update_for_tenant(tenant_id, record_id, values)
        if record is None:
            raise AppError("RECORD_NOT_FOUND", "Record was not found for this tenant.", 404)
        return self._commit(record)

    def _commit(self, record: Any) -> Any:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_RECORD", "A record with these unique values already exists for this tenant.", 409) from exc
        self.db.refresh(record)
        return record

    def _ensure_product_barcode(self, tenant_id: int, product: Product) -> None:
        if product.barcode:
            return
        product.barcode = self._generated_barcode(tenant_id, product.id)

    def _generated_barcode(self, tenant_id: int, product_id: int) -> str:
        return f"88{tenant_id:03d}{product_id:08d}"

    def _product_to_dict(self, product: Product) -> dict[str, Any]:
        return {
            "id": product.id,
            "tenant_id": product.tenant_id,
            "status": product.status,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "category_id": product.category_id,
            "brand_id": product.brand_id,
            "name": product.name,
            "sku": product.sku,
            "barcode": product.barcode,
            "description": product.description,
            "unit": product.unit,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "reorder_level": product.reorder_level,
            "track_batch": product.track_batch,
            "track_expiry": product.track_expiry,
            "track_serial": product.track_serial,
        }

    def _warehouse_name(self, tenant_id: int, warehouse_id: int) -> str:
        warehouse = self.documents.get_warehouse(tenant_id, warehouse_id)
        return warehouse.name if warehouse else f"Warehouse #{warehouse_id}"

    def _location_name(self, tenant_id: int, location_id: int) -> str:
        location = self.documents.get_location(tenant_id, location_id)
        return location.name if location else f"Location #{location_id}"

    def _batch_number_for_serial(self, serial: Any, batches: list[Any]) -> str | None:
        if serial.batch_id is None:
            return None
        for batch in batches:
            if batch.id == serial.batch_id:
                return batch.batch_number
        return None

    def _compact_json(self, value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)

    def _qr_matrix(self, payload: str) -> list[list[bool]]:
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=1, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        return [[bool(cell) for cell in row] for row in qr.get_matrix()]

    def _product_tracking_qr_payload(self, product: Product, *, batch: Any | None = None, serial: Any | None = None) -> str:
        payload: dict[str, Any] = {
            "type": "product",
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "barcode": product.barcode or product.sku or f"PROD-{product.id}",
            "track_batch": bool(product.track_batch),
            "track_expiry": bool(product.track_expiry),
            "track_serial": bool(product.track_serial),
        }
        if batch is not None:
            payload["batch"] = {
                "id": getattr(batch, "id", None),
                "batch_number": getattr(batch, "batch_number", None),
                "supplier_batch_number": getattr(batch, "supplier_batch_number", None),
                "manufacture_date": getattr(batch, "manufacture_date", None),
                "expiry_date": getattr(batch, "expiry_date", None),
                "warranty_until": getattr(batch, "warranty_until", None),
                "status": getattr(batch, "status", None).value if getattr(batch, "status", None) and hasattr(getattr(batch, "status", None), "value") else getattr(batch, "status", None),
            }
        if serial is not None:
            payload["serial"] = {
                "id": getattr(serial, "id", None),
                "serial_number": getattr(serial, "serial_number", None),
                "batch_id": getattr(serial, "batch_id", None),
                "warranty_until": getattr(serial, "warranty_until", None),
                "expires_on": getattr(serial, "expires_on", None),
                "status": getattr(serial, "status", None).value if getattr(serial, "status", None) and hasattr(getattr(serial, "status", None), "value") else getattr(serial, "status", None),
            }
        return self._compact_json(payload)


_CODE39_PATTERNS = {
    "0": "nnnwwnwnn",
    "1": "wnnwnnnnw",
    "2": "nnwwnnnnw",
    "3": "wnwwnnnnn",
    "4": "nnnwwnnnw",
    "5": "wnnwwnnnn",
    "6": "nnwwwnnnn",
    "7": "nnnwnnwnw",
    "8": "wnnwnnwnn",
    "9": "nnwwnnwnn",
    "A": "wnnnnwnnw",
    "B": "nnwnnwnnw",
    "C": "wnwnnwnnn",
    "D": "nnnnwwnnw",
    "E": "wnnnwwnnn",
    "F": "nnwnwwnnn",
    "G": "nnnnnwwnw",
    "H": "wnnnnwwnn",
    "I": "nnwnnwwnn",
    "J": "nnnnwwwnn",
    "K": "wnnnnnnww",
    "L": "nnwnnnnww",
    "M": "wnwnnnnwn",
    "N": "nnnnwnnww",
    "O": "wnnnwnnwn",
    "P": "nnwnwnnwn",
    "Q": "nnnnnnwww",
    "R": "wnnnnnwwn",
    "S": "nnwnnnwwn",
    "T": "nnnnwnwwn",
    "U": "wwnnnnnnw",
    "V": "nwwnnnnnw",
    "W": "wwwnnnnnn",
    "X": "nwnnwnnnw",
    "Y": "wwnnwnnnn",
    "Z": "nwwnwnnnn",
    "-": "nwnnnnwnw",
    ".": "wwnnnnwnn",
    " ": "nwwnnnwnn",
    "$": "nwnwnwnnn",
    "/": "nwnwnnnwn",
    "+": "nwnnnwnwn",
    "%": "nnnwnwnwn",
    "*": "nwnnwnwnn",
}

_FAST_LABEL_PDF_CACHE: OrderedDict[tuple[str, ...], bytes] = OrderedDict()
_FAST_LABEL_PDF_CACHE_MAX = 24


def _pdf_escape_text(value: str) -> str:
    safe = value.encode("latin-1", errors="replace").decode("latin-1")
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text_command(font: str, size: float, x: float, y: float, text: str) -> str:
    return f"BT /{font} {size:.2f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_pdf_escape_text(text)}) Tj ET"


def _pdf_rect_command(x: float, y: float, w: float, h: float, *, fill: bool = False) -> str:
    return f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {'f' if fill else 'S'}"


def _barcode_segments(value: str) -> tuple[list[tuple[bool, float]], float]:
    allowed = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
    normalized = "".join(ch for ch in value.upper() if ch in allowed)
    if not normalized:
        normalized = "WARELYN"
    encoded = f"*{normalized}*"
    narrow = 1.0
    wide = 2.4
    quiet = 4.0
    segments: list[tuple[bool, float]] = []
    total_width = quiet
    for char in encoded:
        pattern = _CODE39_PATTERNS.get(char)
        if pattern is None:
            continue
        for index, symbol in enumerate(pattern):
            width = wide if symbol == "w" else narrow
            segments.append((index % 2 == 0, width))
            total_width += width
        total_width += narrow
    total_width += quiet - narrow
    return segments, total_width


def _build_multi_page_pdf(page_streams: list[str], title: str) -> bytes:
    def _obj(data: bytes | str) -> bytes:
        return data.encode("latin-1", errors="replace") if isinstance(data, str) else data

    page_count = len(page_streams)
    catalog_id = 1
    pages_id = 2
    page_start_id = 3
    content_start_id = page_start_id + page_count
    font1_id = content_start_id + page_count
    font2_id = font1_id + 1
    objects: list[bytes] = []
    kids = " ".join(f"{page_start_id + idx} 0 R" for idx in range(page_count))
    objects.append(_obj(f"1 0 obj << /Type /Catalog /Pages {pages_id} 0 R /Lang (en-US) >> endobj"))
    objects.append(_obj(f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {page_count} >> endobj"))

    for idx, content in enumerate(page_streams):
        page_obj_id = page_start_id + idx
        content_obj_id = content_start_id + idx
        objects.append(_obj(
            f"{page_obj_id} 0 obj << /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595.28 841.89] "
            f"/Resources << /Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R >> >> /Contents {content_obj_id} 0 R >> endobj"
        ))

    for idx, content in enumerate(page_streams):
        stream = content.encode("latin-1", errors="replace")
        content_obj_id = content_start_id + idx
        objects.append(_obj(f"{content_obj_id} 0 obj << /Length {len(stream)} >> stream\n") + stream + b"\nendstream endobj")

    objects.append(_obj(f"{font1_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj"))
    objects.append(_obj(f"{font2_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Courier >> endobj"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b"\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n".encode("latin-1"))
    pdf.extend(f"startxref\n{xref_start}\n%%EOF".encode("latin-1"))
    return bytes(pdf)


class ProductLabelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.documents = DocumentsRepository(db)
        self.inventory = InventoryRepository(db)

    def render_product_labels_pdf(self, tenant_id: int, product_ids: list[int]) -> bytes:
        ids = [int(product_id) for product_id in product_ids if product_id is not None]
        if not ids:
            raise AppError("PRODUCT_IDS_REQUIRED", "Select at least one product to print labels.", 400)
        tenant = self.documents.get_tenant(tenant_id)
        products_by_id = {product.id: product for product in self.products.list_by_tenant(tenant_id) if product.id in set(ids)}
        selected = [products_by_id[product_id] for product_id in ids if product_id in products_by_id]
        if not selected:
            raise AppError("PRODUCTS_NOT_FOUND", "No selected products were found for this tenant.", 404)
        html = self._build_html(tenant.company_name if tenant else "Warelyn", selected)
        return render_html_to_pdf(html)

    def render_tracking_product_labels_pdf(
        self,
        tenant_id: int,
        product_ids: list[int],
        tracking_mode: ProductLabelTrackingMode,
    ) -> bytes:
        ids = [int(product_id) for product_id in product_ids if product_id is not None]
        if not ids:
            raise AppError("PRODUCT_IDS_REQUIRED", "Select at least one product to print labels.", 400)
        tenant = self.documents.get_tenant(tenant_id)
        selected_products = {
            product.id: product
            for product in self.products.list_by_tenant(tenant_id)
            if product.id in set(ids)
        }
        selected = [selected_products[product_id] for product_id in ids if product_id in selected_products]
        selected = [product for product in selected if self._matches_tracking_mode(product, tracking_mode)]
        if not selected:
            raise AppError("PRODUCTS_NOT_FOUND", "No selected products matched the requested tracking mode.", 404)
        html = self._build_html(
            tenant.company_name if tenant else "Warelyn",
            selected,
            heading=self._heading_for_tracking_mode(tracking_mode),
            subtitle=self._subtitle_for_tracking_mode(tracking_mode),
        )
        return render_html_to_pdf(html)

    def render_product_labels_for_product_pdf(self, tenant_id: int, product_id: int) -> bytes:
        product = self.products.get_by_id_for_tenant(tenant_id, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        total_available = self.inventory.total_available_for_product(tenant_id, product_id)
        label_count = int(float(total_available) // 1)
        if label_count <= 0:
            raise AppError("NO_LABEL_QUANTITY", "No available stock exists for this product.", 400)
        tenant = self.documents.get_tenant(tenant_id)
        company_name = tenant.company_name if tenant else "Warelyn"
        cache_key = (
            str(tenant_id),
            str(product.id),
            str(product.updated_at.isoformat() if getattr(product, "updated_at", None) else ""),
            company_name,
            product.name,
            product.sku,
            product.barcode or "",
            str(product.track_batch),
            str(product.track_expiry),
            str(product.track_serial),
            str(label_count),
            str(total_available),
        )
        cached = _FAST_LABEL_PDF_CACHE.get(cache_key)
        if cached is not None:
            _FAST_LABEL_PDF_CACHE.move_to_end(cache_key)
            return cached

        pdf_bytes = self._build_fast_product_labels_pdf(company_name, product, label_count)
        _FAST_LABEL_PDF_CACHE[cache_key] = pdf_bytes
        _FAST_LABEL_PDF_CACHE.move_to_end(cache_key)
        while len(_FAST_LABEL_PDF_CACHE) > _FAST_LABEL_PDF_CACHE_MAX:
            _FAST_LABEL_PDF_CACHE.popitem(last=False)
        return pdf_bytes

    def _compact_json(self, value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)

    def _qr_matrix(self, payload: str) -> list[list[bool]]:
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=1, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        return [[bool(cell) for cell in row] for row in qr.get_matrix()]

    def _product_tracking_qr_payload(self, product: Product, *, batch: Any | None = None, serial: Any | None = None) -> str:
        payload: dict[str, Any] = {
            "type": "product",
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "barcode": product.barcode or product.sku or f"PROD-{product.id}",
            "track_batch": bool(product.track_batch),
            "track_expiry": bool(product.track_expiry),
            "track_serial": bool(product.track_serial),
        }
        if batch is not None:
            payload["batch"] = {
                "id": getattr(batch, "id", None),
                "batch_number": getattr(batch, "batch_number", None),
                "supplier_batch_number": getattr(batch, "supplier_batch_number", None),
                "manufacture_date": getattr(batch, "manufacture_date", None),
                "expiry_date": getattr(batch, "expiry_date", None),
                "warranty_until": getattr(batch, "warranty_until", None),
                "status": getattr(batch, "status", None).value if getattr(batch, "status", None) and hasattr(getattr(batch, "status", None), "value") else getattr(batch, "status", None),
            }
        if serial is not None:
            payload["serial"] = {
                "id": getattr(serial, "id", None),
                "serial_number": getattr(serial, "serial_number", None),
                "batch_id": getattr(serial, "batch_id", None),
                "warranty_until": getattr(serial, "warranty_until", None),
                "expires_on": getattr(serial, "expires_on", None),
                "status": getattr(serial, "status", None).value if getattr(serial, "status", None) and hasattr(getattr(serial, "status", None), "value") else getattr(serial, "status", None),
            }
        return self._compact_json(payload)

    def _draw_qr_matrix(self, page_commands: list[str], matrix: list[list[bool]], x: float, y: float, size: float) -> None:
        if not matrix:
            return
        rows = len(matrix)
        cols = max((len(row) for row in matrix), default=0)
        if rows == 0 or cols == 0:
            return
        cell = size / max(rows, cols)
        draw_width = cols * cell
        draw_height = rows * cell
        offset_x = x + max(0.0, (size - draw_width) / 2)
        offset_y = y + max(0.0, (size - draw_height) / 2)
        for row_index, row in enumerate(matrix):
            for col_index, cell_on in enumerate(row):
                if not cell_on:
                    continue
                cell_x = offset_x + col_index * cell
                cell_y = offset_y + (rows - row_index - 1) * cell
                page_commands.append(_pdf_rect_command(cell_x, cell_y, cell, cell, fill=True))

    def _build_fast_product_labels_pdf(self, company_name: str, product: Product, label_count: int) -> bytes:
        page_width = 595.28
        page_height = 841.89
        margin = 18.0
        gap = 8.0
        columns = 2
        rows = 4
        label_width = (page_width - (margin * 2) - gap) / columns
        label_height = (page_height - (margin * 2) - (gap * (rows - 1))) / rows
        labels_per_page = columns * rows
        barcode_value = (product.barcode or product.sku or f"PROD-{product.id}").strip()
        tracking_text = self._tracking_text(product)
        product_name_lines = wrap(product.name, width=22)[:2] or [product.name]
        if len(product_name_lines) == 1 and len(product_name_lines[0]) > 26:
            product_name_lines = [product_name_lines[0][:26]]
        qr_payload = self._product_tracking_qr_payload(product)
        qr_matrix = self._qr_matrix(qr_payload)

        pages: list[str] = []
        for start in range(0, label_count, labels_per_page):
            page_commands = ["0 0 0 rg", "0 0 0 RG"]
            chunk_size = min(labels_per_page, label_count - start)
            for index in range(chunk_size):
                col = index % columns
                row = index // columns
                x = margin + col * (label_width + gap)
                y = page_height - margin - (row + 1) * label_height - row * gap
                page_commands.append("q")
                page_commands.append(_pdf_rect_command(x, y, label_width, label_height))
                page_commands.append(_pdf_text_command("F1", 8, x + 8, y + label_height - 16, company_name))
                qr_size = 56.0
                qr_x = x + label_width - qr_size - 8.0
                qr_y = y + label_height - qr_size - 10.0
                page_commands.append("0 0 0 rg")
                self._draw_qr_matrix(page_commands, qr_matrix, qr_x, qr_y, qr_size)
                for line_index, line in enumerate(product_name_lines):
                    page_commands.append(_pdf_text_command("F1", 11 if line_index == 0 else 10, x + 8, y + label_height - 32 - (line_index * 12), line))
                page_commands.append(_pdf_text_command("F2", 7.5, x + 8, y + label_height - 58, f"SKU: {product.sku}"))
                page_commands.append(_pdf_text_command("F2", 7.5, x + 8, y + label_height - 69, f"Barcode: {product.barcode or 'N/A'}"))
                page_commands.append(_pdf_text_command("F2", 7.5, x + 8, y + label_height - 80, f"Tracking: {tracking_text}"))
                segments, total_width = _barcode_segments(barcode_value)
                barcode_max_width = label_width - 16.0
                scale = min(1.0, barcode_max_width / total_width) if total_width > 0 else 1.0
                scaled_width = total_width * scale
                barcode_x = x + max(8.0, (label_width - scaled_width) / 2)
                barcode_y = y + 18.0
                cursor = barcode_x
                for is_bar, width in segments:
                    scaled = width * scale
                    if is_bar:
                        page_commands.append(_pdf_rect_command(cursor, barcode_y, scaled, 24.0, fill=True))
                    cursor += scaled
                page_commands.append(_pdf_text_command("F2", 5.8, x + 8, y + 6, barcode_value))
                page_commands.append("Q")
            pages.append("\n".join(page_commands))

        return _build_multi_page_pdf(pages, title=f"{company_name} product labels")

    def _build_html(self, company_name: str, products: list[Product], heading: str | None = None, subtitle: str | None = None) -> str:
        cards = "".join(self._render_label_card(product) for product in products)
        return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Product Labels</title>
    <style>
      @page {{ size: A4; margin: 10mm; }}
      body {{
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        color: #111827;
        background: white;
      }}
      .sheet-title {{
        margin: 0 0 4mm 0;
        font-size: 16px;
        font-weight: 700;
      }}
      .sheet-subtitle {{
        margin: 0 0 8mm 0;
        font-size: 10px;
        color: #6b7280;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6mm;
      }}
      .label {{
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
        padding: 5mm;
        min-height: 40mm;
        page-break-inside: avoid;
        overflow: hidden;
      }}
      .label-company {{
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #2563eb;
        font-weight: 700;
        margin-bottom: 1.5mm;
      }}
      .label-name {{
        font-size: 12px;
        font-weight: 700;
        margin: 0 0 1.5mm 0;
        line-height: 1.25;
      }}
      .label-meta {{
        display: flex;
        gap: 2mm;
        flex-wrap: wrap;
        font-size: 9px;
        color: #4b5563;
        margin-bottom: 2mm;
      }}
      .label-chip {{
        display: inline-block;
        border-radius: 999px;
        padding: 1px 6px;
        background: #eff6ff;
        color: #1d4ed8;
      }}
      .barcode svg {{
        width: 100%;
        height: auto;
        display: block;
      }}
    </style>
  </head>
  <body>
    <h1 class="sheet-title">{escape(heading or f"{company_name} product labels")}</h1>
    <p class="sheet-subtitle">{escape(subtitle or "Print-ready labels with SKU and barcode for the selected products.")}</p>
    <div class="grid">
      {cards}
    </div>
  </body>
</html>
        """

    def _render_label_card(self, product: Product) -> str:
        barcode_value = (product.barcode or product.sku or f"PROD-{product.id}").strip()
        barcode_svg = self._barcode_svg(barcode_value)
        tracking_text = self._tracking_text(product)
        return f"""
        <div class="label">
          <div class="label-company">Warelyn</div>
          <p class="label-name">{escape(product.name)}</p>
          <div class="label-meta">
            <span class="label-chip">SKU: {escape(product.sku)}</span>
            <span class="label-chip">Barcode: {escape(product.barcode or 'N/A')}</span>
            <span class="label-chip">Tracking: {escape(tracking_text)}</span>
          </div>
          <div class="barcode">{barcode_svg}</div>
        </div>
        """

    def _tracking_text(self, product: Product) -> str:
        flags = [
            label
            for enabled, label in (
                (product.track_batch, "Batch"),
                (product.track_expiry, "Expiry"),
                (product.track_serial, "Serial"),
            )
            if enabled
        ]
        return ", ".join(flags) if flags else "Standard"

    def _tracking_mode_for_product(self, product: Product) -> ProductLabelTrackingMode:
        if product.track_serial:
            return ProductLabelTrackingMode.SERIAL
        if product.track_expiry:
            return ProductLabelTrackingMode.EXPIRY
        if product.track_batch:
            return ProductLabelTrackingMode.BATCH
        return ProductLabelTrackingMode.STANDARD

    def _matches_tracking_mode(self, product: Product, tracking_mode: ProductLabelTrackingMode) -> bool:
        if tracking_mode == ProductLabelTrackingMode.ALL:
            return True
        if tracking_mode == ProductLabelTrackingMode.TRACKED:
            return bool(product.track_batch or product.track_expiry or product.track_serial)
        if tracking_mode == ProductLabelTrackingMode.STANDARD:
            return not (product.track_batch or product.track_expiry or product.track_serial)
        if tracking_mode == ProductLabelTrackingMode.BATCH:
            return bool(product.track_batch)
        if tracking_mode == ProductLabelTrackingMode.EXPIRY:
            return bool(product.track_expiry)
        if tracking_mode == ProductLabelTrackingMode.SERIAL:
            return bool(product.track_serial)
        return True

    def _heading_for_tracking_mode(self, tracking_mode: ProductLabelTrackingMode) -> str:
        if tracking_mode == ProductLabelTrackingMode.ALL:
            return "Warelyn product labels"
        return f"{tracking_mode.value.replace('_', ' ').title()} product labels"

    def _subtitle_for_tracking_mode(self, tracking_mode: ProductLabelTrackingMode) -> str:
        if tracking_mode == ProductLabelTrackingMode.ALL:
            return "Print-ready labels with SKU, barcode, and tracking details for the selected products."
        return f"Print-ready labels for selected {tracking_mode.value.replace('_', ' ').lower()}-tracked products."

    def _barcode_svg(self, value: str) -> str:
        allowed = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
        normalized = "".join(ch for ch in value.upper() if ch in allowed)
        if not normalized:
            normalized = "WARELYN"
        encoded = f"*{normalized}*"
        narrow = 2
        wide = 5
        quiet = 10
        bar_height = 44
        x = quiet
        bars: list[str] = []
        for char in encoded:
            pattern = _CODE39_PATTERNS.get(char)
            if pattern is None:
                continue
            for index, symbol in enumerate(pattern):
                width = wide if symbol == "w" else narrow
                if index % 2 == 0:
                    bars.append(f'<rect x="{x}" y="0" width="{width}" height="{bar_height}" fill="#111827" />')
                x += width
            x += narrow
        width = x + quiet - narrow
        human = escape(value)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {bar_height + 16}" role="img" aria-label="Barcode for {human}">'
            f'<rect width="100%" height="100%" fill="white" />'
            f'{"".join(bars)}'
            f'<text x="{width / 2}" y="{bar_height + 12}" text-anchor="middle" font-family="monospace" font-size="10" fill="#111827">{human}</text>'
            f"</svg>"
        )


class WarehouseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.warehouses = WarehouseRepository(db)
        self.locations = WarehouseLocationRepository(db)

    def list_warehouses(self, tenant_id: int) -> list[Warehouse]:
        return self.warehouses.list_by_tenant(tenant_id)

    def create_warehouse(self, tenant_id: int, values: dict[str, Any]) -> Warehouse:
        return self._commit(self.warehouses.create_for_tenant(tenant_id, values))

    def update_warehouse(self, tenant_id: int, warehouse_id: int, values: dict[str, Any]) -> Warehouse:
        record = self.warehouses.update_for_tenant(tenant_id, warehouse_id, values)
        if record is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)
        return self._commit(record)

    def list_locations(self, tenant_id: int, warehouse_id: int) -> list[WarehouseLocation]:
        self._require_warehouse(tenant_id, warehouse_id)
        return self.locations.list_for_warehouse(tenant_id, warehouse_id)

    def create_location(self, tenant_id: int, warehouse_id: int, values: dict[str, Any]) -> WarehouseLocation:
        self._require_warehouse(tenant_id, warehouse_id)
        self._validate_parent(tenant_id, warehouse_id, values)
        return self._commit(self.locations.create_for_tenant(tenant_id, {**values, "warehouse_id": warehouse_id}))

    def update_location(self, tenant_id: int, warehouse_id: int, location_id: int, values: dict[str, Any]) -> WarehouseLocation:
        self._require_warehouse(tenant_id, warehouse_id)
        self._validate_parent(tenant_id, warehouse_id, values)
        record = self.locations.get_for_warehouse(tenant_id, warehouse_id, location_id)
        if record is None:
            raise AppError("LOCATION_NOT_FOUND", "Warehouse location was not found for this tenant.", 404)
        for key, value in values.items():
            setattr(record, key, value)
        return self._commit(record)

    def _require_warehouse(self, tenant_id: int, warehouse_id: int) -> Warehouse:
        warehouse = self.warehouses.get_by_id_for_tenant(tenant_id, warehouse_id)
        if warehouse is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)
        return warehouse

    def _validate_parent(self, tenant_id: int, warehouse_id: int, values: dict[str, Any]) -> None:
        parent_id = values.get("parent_location_id")
        if parent_id and self.locations.get_for_warehouse(tenant_id, warehouse_id, parent_id) is None:
            raise AppError("PARENT_LOCATION_NOT_FOUND", "Parent location was not found for this warehouse.", 404)

    def _commit(self, record: Any) -> Any:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_RECORD", "A record with these unique values already exists for this tenant.", 409) from exc
        self.db.refresh(record)
        return record
