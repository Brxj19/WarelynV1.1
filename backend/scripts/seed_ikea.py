"""
Seed script for an IKEA tenant with realistic catalog, stock, and workflow history.
Run from backend/: .venv/bin/python scripts/seed_ikea.py

Append-only and idempotent:
- keeps existing data untouched
- creates an IKEA tenant if missing
- seeds workflow-rich data with tracking-aware products
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seed_minimalist as base_seed
from scripts.bootstrap_migrations import upgrade_database
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.documents import Bill, Invoice
from app.models.fulfillment import PickTask, PickTaskStatus
from app.models.inventory import WarehouseStock
from app.models.master_data import Brand, Category, Customer, LocationType, Product, RecordStatus, Vendor, Warehouse, WarehouseLocation
from app.models.operations import PutawayTask, ReorderRule, StockCountSession
from app.models.purchasing import PurchaseOrder, PurchaseReceipt
from app.models.returns import SalesReturn
from app.models.returns import SalesReturnItemStatus
from app.models.sales import SalesFulfillment, SalesOrder
from app.models.workflow import WorkflowEvent, WorkflowTask
from app.repositories.fulfillment import FulfillmentRepository
from app.services.documents import DocumentsService
from app.services.fulfillment import FulfillmentService
from app.services.operations import CycleCountService
from app.services.purchasing import PurchasingService
from app.services.returns import ReturnsService
from app.services.sales import SalesService


SEED_TAG = "IKEA-SEED-2026Q2"
IKEA_TENANT_NAME = "IKEA"
IKEA_ADMIN_EMAIL = "admin@ikea.com"
IKEA_ADMIN_PASSWORD = "Ikea@12345"
IKEA_SHARED_USER_PASSWORD = "Ikea@12345"


def as_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def upsert_tenant_and_admin(db: Session) -> tuple[Tenant, User]:
    tenant = db.query(Tenant).filter(Tenant.company_name == IKEA_TENANT_NAME).order_by(Tenant.id.asc()).first()
    admin = db.query(User).filter(User.email == IKEA_ADMIN_EMAIL).first()

    if tenant is None and admin and admin.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()

    if tenant is None:
        tenant = Tenant(
            company_name=IKEA_TENANT_NAME,
            contact_email=IKEA_ADMIN_EMAIL,
            phone="+46-8-123-4567",
            address="Älmhult, Sweden",
            business_type="Furniture & Home Furnishings",
            status=TenantStatus.ACTIVE,
        )
        db.add(tenant)
        db.flush()

    if admin is None:
        admin = User(
            tenant_id=tenant.id,
            name="IKEA Tenant Admin",
            email=IKEA_ADMIN_EMAIL,
            phone="+46-8-123-4568",
            password_hash=get_password_hash(IKEA_ADMIN_PASSWORD),
            role=UserRole.TENANT_ADMIN,
            status=UserStatus.ACTIVE,
            email_verified_at=datetime.now(UTC),
        )
        db.add(admin)
        db.flush()
    else:
        admin.tenant_id = tenant.id
        admin.password_hash = get_password_hash(IKEA_ADMIN_PASSWORD)
        admin.status = UserStatus.ACTIVE
        db.flush()

    return tenant, admin


def seed_categories(db: Session, tenant_id: int) -> dict[str, int]:
    categories = [
        ("Living Room", "Sofas, tables, storage, and seating"),
        ("Bedroom", "Beds, wardrobes, nightstands, and mattresses"),
        ("Kitchen & Dining", "Dining tables, chairs, storage, and serving"),
        ("Storage", "Shelves, boxes, and organizers"),
        ("Lighting", "Lamps, bulbs, and smart lighting"),
        ("Décor", "Candles, plants, frames, and textiles"),
        ("Office", "Desks, chairs, and accessories"),
        ("Outdoor", "Patio, balcony, and garden furnishings"),
    ]
    result: dict[str, int] = {}
    for name, description in categories:
        existing = db.query(Category).filter(Category.tenant_id == tenant_id, Category.name == name).first()
        if existing is None:
            row = Category(tenant_id=tenant_id, name=name, description=description)
            db.add(row)
            db.flush()
            result[name] = row.id
        else:
            result[name] = existing.id
    return result


def seed_brands(db: Session, tenant_id: int) -> dict[str, int]:
    brands = [
        ("IKEA", "IKEA core furniture assortment"),
        ("TRÅDFRI", "Smart home and lighting line"),
        ("FÖRNUFT", "Home accessories and décor"),
    ]
    result: dict[str, int] = {}
    for name, description in brands:
        existing = db.query(Brand).filter(Brand.tenant_id == tenant_id, Brand.name == name).first()
        if existing is None:
            row = Brand(tenant_id=tenant_id, name=name, description=description)
            db.add(row)
            db.flush()
            result[name] = row.id
        else:
            result[name] = existing.id
    return result


def seed_vendors(db: Session, tenant_id: int) -> dict[str, int]:
    vendors = [
        {"name": "Nordic Timberworks AB", "email": "orders@nordictimberworks.se", "phone": "+46-40-555-0101", "address": "Malmö, Sweden", "gst_number": "SE5566778899"},
        {"name": "Scandi Pack Solutions", "email": "supply@scandipack.eu", "phone": "+46-31-555-0199", "address": "Gothenburg, Sweden", "gst_number": "SE9988776655"},
        {"name": "Lumen Components Europe", "email": "sales@lumencomponents.eu", "phone": "+49-30-555-0244", "address": "Berlin, Germany", "gst_number": "DE123456789"},
        {"name": "NorthStar Textiles", "email": "procurement@northstartextiles.se", "phone": "+46-8-555-0322", "address": "Stockholm, Sweden", "gst_number": "SE1122334455"},
        {"name": "Scandi Logistics Network", "email": "dispatch@scandilogistics.se", "phone": "+46-8-555-0444", "address": "Stockholm, Sweden", "gst_number": "SE6677889900"},
    ]
    result: dict[str, int] = {}
    for vendor in vendors:
        existing = db.query(Vendor).filter(Vendor.tenant_id == tenant_id, Vendor.name == vendor["name"]).first()
        if existing is None:
            row = Vendor(tenant_id=tenant_id, **vendor)
            db.add(row)
            db.flush()
            result[vendor["name"]] = row.id
        else:
            result[vendor["name"]] = existing.id
    return result


def seed_customers(db: Session, tenant_id: int) -> dict[str, int]:
    customers = [
        {"name": "IKEA Online Store", "email": "orders@ikea-online.example", "phone": "+46-8-555-1001", "address": "Älmhult, Sweden", "gst_number": "SE2223334445"},
        {"name": "Scandinavian Home Retail", "email": "procurement@scandihome.example", "phone": "+46-8-555-1002", "address": "Stockholm, Sweden", "gst_number": "SE3334445556"},
        {"name": "Nordic Living Concepts", "email": "purchasing@nordicliving.example", "phone": "+46-8-555-1003", "address": "Copenhagen, Denmark", "gst_number": "DK4445556667"},
        {"name": "Urban Apartment Supply", "email": "buyers@urbanapt.example", "phone": "+46-8-555-1004", "address": "Oslo, Norway", "gst_number": "NO5556667778"},
        {"name": "Campus Housing Group", "email": "ops@campushousing.example", "phone": "+46-8-555-1005", "address": "Helsinki, Finland", "gst_number": "FI6667778889"},
    ]
    result: dict[str, int] = {}
    for customer in customers:
        existing = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.email == customer["email"]).first()
        if existing is None:
            row = Customer(tenant_id=tenant_id, **customer)
            db.add(row)
            db.flush()
            result[customer["name"]] = row.id
        else:
            result[customer["name"]] = existing.id
    return result


def seed_products(db: Session, tenant_id: int, categories: dict[str, int], brands: dict[str, int]) -> dict[str, int]:
    textiles_category_id = categories.get("Textiles") or categories["Décor"]
    if "Textiles" not in categories:
        textiles = db.query(Category).filter(Category.tenant_id == tenant_id, Category.name == "Textiles").first()
        if textiles is None:
            textiles = Category(tenant_id=tenant_id, name="Textiles", description="Bath and home textiles")
            db.add(textiles)
            db.flush()
        categories["Textiles"] = textiles.id
        textiles_category_id = textiles.id

    products = [
        {"name": "BILLY Bookcase", "sku": "IKEA-LV-001", "barcode": "7312340000011", "category_id": categories["Living Room"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("42.00"), "selling_price": Decimal("79.00"), "reorder_level": 180, "description": "Classic bookcase for living rooms and offices"},
        {"name": "LACK Side Table", "sku": "IKEA-LV-002", "barcode": "7312340000028", "category_id": categories["Living Room"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("12.50"), "selling_price": Decimal("19.00"), "reorder_level": 300, "description": "Lightweight side table with simple lines"},
        {"name": "POÄNG Armchair", "sku": "IKEA-LV-003", "barcode": "7312340000035", "category_id": categories["Living Room"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("58.00"), "selling_price": Decimal("109.00"), "reorder_level": 120, "description": "Bentwood armchair with removable cushion"},
        {"name": "MALM Bed Frame", "sku": "IKEA-BD-001", "barcode": "7312340000042", "category_id": categories["Bedroom"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("145.00"), "selling_price": Decimal("299.00"), "reorder_level": 90, "description": "Minimal bed frame with storage-ready profile"},
        {"name": "KALLAX Shelf Unit", "sku": "IKEA-ST-001", "barcode": "7312340000059", "category_id": categories["Storage"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("28.00"), "selling_price": Decimal("55.00"), "reorder_level": 200, "description": "Flexible cube storage shelf unit"},
        {"name": "RÅSKOG Utility Cart", "sku": "IKEA-ST-002", "barcode": "7312340000066", "category_id": categories["Storage"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("14.00"), "selling_price": Decimal("29.00"), "reorder_level": 250, "description": "Mobile utility cart for kitchens and offices"},
        {"name": "SINNERLIG Scented Candle Pack", "sku": "IKEA-DC-001", "barcode": "7312340000073", "category_id": categories["Décor"], "brand_id": brands["FÖRNUFT"], "unit": "pcs", "cost_price": Decimal("4.00"), "selling_price": Decimal("9.00"), "reorder_level": 600, "description": "Decorative candles with lot and expiry tracking", "track_batch": True, "track_expiry": True},
        {"name": "LEDARE LED Bulb Pack", "sku": "IKEA-LG-001", "barcode": "7312340000080", "category_id": categories["Lighting"], "brand_id": brands["TRÅDFRI"], "unit": "pcs", "cost_price": Decimal("6.50"), "selling_price": Decimal("12.00"), "reorder_level": 550, "description": "Energy-saving bulbs with expiry-aware stock", "track_batch": True, "track_expiry": True},
        {"name": "TRÅDFRI Smart Bulb", "sku": "IKEA-LG-002", "barcode": "7312340000097", "category_id": categories["Lighting"], "brand_id": brands["TRÅDFRI"], "unit": "pcs", "cost_price": Decimal("8.00"), "selling_price": Decimal("16.00"), "reorder_level": 400, "description": "Smart bulb with serial-level traceability", "track_serial": True},
        {"name": "FEJKA Artificial Plant", "sku": "IKEA-DC-002", "barcode": "7312340000103", "category_id": categories["Décor"], "brand_id": brands["FÖRNUFT"], "unit": "pcs", "cost_price": Decimal("7.00"), "selling_price": Decimal("15.00"), "reorder_level": 220, "description": "Decorative plant for modern interiors"},
        {"name": "FRAKTA Storage Bag", "sku": "IKEA-ST-003", "barcode": "7312340000110", "category_id": categories["Storage"], "brand_id": brands["IKEA"], "unit": "pcs", "cost_price": Decimal("1.20"), "selling_price": Decimal("2.50"), "reorder_level": 1000, "description": "Reusable blue bag for moving and storage"},
        {"name": "VÅGSJÖN Towel Set", "sku": "IKEA-TE-001", "barcode": "7312340000127", "category_id": textiles_category_id, "brand_id": brands["IKEA"], "unit": "set", "cost_price": Decimal("9.50"), "selling_price": Decimal("19.00"), "reorder_level": 260, "description": "Bathroom towel set with lot traceability", "track_batch": True},
    ]
    result: dict[str, int] = {}
    for product in products:
        existing = db.query(Product).filter(Product.tenant_id == tenant_id, Product.sku == product["sku"]).first()
        if existing is None:
            row = Product(tenant_id=tenant_id, **product)
            db.add(row)
            db.flush()
            result[product["sku"]] = row.id
        else:
            result[product["sku"]] = existing.id
    return result


def seed_warehouses(db: Session, tenant_id: int) -> dict[str, dict[str, Any]]:
    warehouses = [
        {
            "name": "Stockholm Central DC",
            "code": "STH-DC",
            "address": "Rosersberg, Stockholm County, Sweden",
            "locations": [
                {"name": "Receiving Dock", "code": "STH-RCV", "location_type": LocationType.RECEIVING},
                {"name": "Main Storage", "code": "STH-STR", "location_type": LocationType.STORAGE},
                {"name": "Pick Zone", "code": "STH-PICK", "location_type": LocationType.PICKING},
                {"name": "Packing", "code": "STH-PACK", "location_type": LocationType.PACKING},
                {"name": "Shipping", "code": "STH-SHIP", "location_type": LocationType.SHIPPING},
                {"name": "Returns", "code": "STH-RET", "location_type": LocationType.RETURN},
                {"name": "QC", "code": "STH-QC", "location_type": LocationType.QC},
                {"name": "Damaged", "code": "STH-DMG", "location_type": LocationType.DAMAGED},
            ],
        },
        {
            "name": "Bengaluru Market Hub",
            "code": "BLR-HUB",
            "address": "Whitefield, Bengaluru, India",
            "locations": [
                {"name": "Receiving", "code": "BLR-RCV", "location_type": LocationType.RECEIVING},
                {"name": "Storage", "code": "BLR-STR", "location_type": LocationType.STORAGE},
                {"name": "Picking", "code": "BLR-PICK", "location_type": LocationType.PICKING},
                {"name": "Packing", "code": "BLR-PACK", "location_type": LocationType.PACKING},
                {"name": "Shipping", "code": "BLR-SHIP", "location_type": LocationType.SHIPPING},
                {"name": "Returns", "code": "BLR-RET", "location_type": LocationType.RETURN},
            ],
        },
        {
            "name": "Delhi NCR Hub",
            "code": "DEL-HUB",
            "address": "Noida, Uttar Pradesh, India",
            "locations": [
                {"name": "Inbound", "code": "DEL-RCV", "location_type": LocationType.RECEIVING},
                {"name": "Storage", "code": "DEL-STR", "location_type": LocationType.STORAGE},
                {"name": "Picking", "code": "DEL-PICK", "location_type": LocationType.PICKING},
                {"name": "Packing", "code": "DEL-PACK", "location_type": LocationType.PACKING},
                {"name": "Shipping", "code": "DEL-SHIP", "location_type": LocationType.SHIPPING},
            ],
        },
    ]

    result: dict[str, dict[str, Any]] = {}
    for wh_data in warehouses:
        locations_data = wh_data.pop("locations")
        existing = db.query(Warehouse).filter(Warehouse.tenant_id == tenant_id, Warehouse.code == wh_data["code"]).first()
        if existing is None:
            wh = Warehouse(tenant_id=tenant_id, **wh_data)
            db.add(wh)
            db.flush()
        else:
            wh = existing
        loc_map: dict[str, int] = {}
        for loc_data in locations_data:
            existing_loc = db.query(WarehouseLocation).filter(
                WarehouseLocation.tenant_id == tenant_id,
                WarehouseLocation.warehouse_id == wh.id,
                WarehouseLocation.code == loc_data["code"],
            ).first()
            if existing_loc is None:
                loc = WarehouseLocation(tenant_id=tenant_id, warehouse_id=wh.id, **loc_data)
                db.add(loc)
                db.flush()
                loc_map[loc_data["code"]] = loc.id
            else:
                loc_map[loc_data["code"]] = existing_loc.id
        result[wh.code] = {"id": wh.id, "locations": loc_map}
        wh_data["locations"] = locations_data
    return result


def seed_reorder_rules(db: Session, tenant_id: int, products: dict[str, int], warehouses: dict[str, dict[str, Any]]) -> None:
    wh_id = warehouses["STH-DC"]["id"]
    rules = [
        ("IKEA-LV-001", 180, 800, 120),
        ("IKEA-LV-002", 300, 1200, 200),
        ("IKEA-LV-003", 120, 600, 90),
        ("IKEA-BD-001", 90, 400, 50),
        ("IKEA-ST-001", 200, 800, 150),
        ("IKEA-LG-001", 550, 2200, 250),
        ("IKEA-LG-002", 400, 1500, 200),
        ("IKEA-DC-001", 600, 3000, 250),
    ]
    for sku, min_qty, max_qty, safety in rules:
        product_id = products.get(sku)
        if not product_id:
            continue
        existing = db.query(ReorderRule).filter(
            ReorderRule.tenant_id == tenant_id,
            ReorderRule.product_id == product_id,
            ReorderRule.warehouse_id == wh_id,
        ).first()
        if existing is None:
            db.add(
                ReorderRule(
                    tenant_id=tenant_id,
                    product_id=product_id,
                    warehouse_id=wh_id,
                    min_quantity=Decimal(str(min_qty)),
                    max_quantity=Decimal(str(max_qty)),
                    safety_stock=Decimal(str(safety)),
                    is_active=True,
                )
            )


def seed_stock(db: Session, tenant_id: int, admin_id: int, products: dict[str, int], warehouses: dict[str, dict[str, Any]]) -> int:
    from app.services.inventory import InventoryService

    inv = InventoryService(db)
    plan = [
        {"sku": "IKEA-LV-001", "wh": "STH-DC", "loc": "STH-STR", "qty": 420},
        {"sku": "IKEA-LV-002", "wh": "STH-DC", "loc": "STH-STR", "qty": 720},
        {"sku": "IKEA-LV-003", "wh": "STH-DC", "loc": "STH-STR", "qty": 250},
        {"sku": "IKEA-BD-001", "wh": "STH-DC", "loc": "STH-STR", "qty": 160},
        {"sku": "IKEA-ST-001", "wh": "STH-DC", "loc": "STH-STR", "qty": 540},
        {"sku": "IKEA-ST-002", "wh": "STH-DC", "loc": "STH-STR", "qty": 860},
        {"sku": "IKEA-DC-002", "wh": "BLR-HUB", "loc": "BLR-STR", "qty": 260},
        {"sku": "IKEA-TE-001", "wh": "DEL-HUB", "loc": "DEL-STR", "qty": 180, "batch_number": f"{SEED_TAG}-TE-001", "expiry_date": date.today() + timedelta(days=540), "manufacture_date": date.today() - timedelta(days=30)},
    ]
    stocked = 0
    for entry in plan:
        sku = entry["sku"]
        product_id = products.get(sku)
        if not product_id:
            continue
        warehouse = warehouses[entry["wh"]]
        loc_id = warehouse["locations"].get(entry["loc"])
        if not loc_id:
            continue
        try:
            payload = {
                "product_id": product_id,
                "warehouse_id": warehouse["id"],
                "location_id": loc_id,
                "quantity": str(entry["qty"]),
                "idempotency_key": f"{SEED_TAG}:stock:{sku}:{entry['wh']}:{entry['loc']}",
            }
            if entry.get("batch_number"):
                payload["batch_number"] = entry["batch_number"]
                payload["expiry_date"] = entry.get("expiry_date")
                payload["manufacture_date"] = entry.get("manufacture_date")
            inv.stock_in(tenant_id, admin_id, payload)
            stocked += 1
        except Exception:
            pass
    return stocked


def ensure_role_users(db: Session, tenant_id: int) -> dict[str, User]:
    users_to_seed = [
        {"name": "IKEA Inventory Lead", "email": "inventory@ikea.com", "role": UserRole.INVENTORY_MANAGER},
        {"name": "IKEA Sales Lead", "email": "sales@ikea.com", "role": UserRole.SALES_STAFF},
        {"name": "IKEA Purchase Lead", "email": "purchasing@ikea.com", "role": UserRole.PURCHASE_STAFF},
        {"name": "IKEA Viewer", "email": "viewer@ikea.com", "role": UserRole.VIEWER},
    ]
    out: dict[str, User] = {}
    for user_data in users_to_seed:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        if user is None:
            user = User(
                tenant_id=tenant_id,
                name=user_data["name"],
                email=user_data["email"],
                password_hash=get_password_hash(IKEA_SHARED_USER_PASSWORD),
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            db.flush()
        else:
            user.tenant_id = tenant_id
            user.password_hash = get_password_hash(IKEA_SHARED_USER_PASSWORD)
            user.status = UserStatus.ACTIVE
        out[user_data["role"].value] = user
    db.commit()
    return out


def load_products(db: Session, tenant_id: int) -> dict[str, Product]:
    rows = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    return {row.sku: row for row in rows}


def receipt_by_number(db: Session, tenant_id: int, number: str) -> PurchaseReceipt | None:
    return base_seed.receipt_by_number(db, tenant_id, number)


def purchase_order_by_number(db: Session, tenant_id: int, number: str) -> PurchaseOrder | None:
    return base_seed.purchase_order_by_number(db, tenant_id, number)


def sales_order_by_number(db: Session, tenant_id: int, number: str) -> SalesOrder | None:
    return base_seed.sales_order_by_number(db, tenant_id, number)


def return_by_number(db: Session, tenant_id: int, number: str) -> SalesReturn | None:
    return base_seed.return_by_number(db, tenant_id, number)


def seed_purchase_workflows(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    products_by_sku: dict[str, Product],
    vendors: dict[str, int],
    warehouses: dict[str, dict[str, Any]],
) -> dict[str, PurchaseOrder]:
    purchasing = PurchasingService(db)
    docs = DocumentsService(db)
    purchase_user = users_by_role["PURCHASE_STAFF"]
    inventory_user = users_by_role["INVENTORY_MANAGER"]
    admin_user = users_by_role["TENANT_ADMIN"]
    today = date.today()

    plans = [
        {
            "number": "IKEA-PO-2026-001",
            "vendor": "Nordic Timberworks AB",
            "days_ago": 24,
            "expected_in_days": 5,
            "items": [("IKEA-LV-001", 320, "39.50"), ("IKEA-LV-002", 500, "11.75"), ("IKEA-ST-001", 220, "24.20")],
            "submit": True,
        },
        {
            "number": "IKEA-PO-2026-002",
            "vendor": "Scandi Pack Solutions",
            "days_ago": 20,
            "expected_in_days": 1,
            "items": [("IKEA-DC-001", 700, "3.75"), ("IKEA-DC-002", 240, "6.10")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "IKEA-RCPT-2026-002-A",
                    "wh_code": "STH-DC",
                    "loc_code": "STH-RCV",
                    "lines": [("IKEA-DC-001", 420), ("IKEA-DC-002", 140)],
                    "batch": True,
                    "complete_putaway": 1,
                }
            ],
        },
        {
            "number": "IKEA-PO-2026-003",
            "vendor": "Lumen Components Europe",
            "days_ago": 16,
            "expected_in_days": 2,
            "items": [("IKEA-LG-001", 600, "5.90"), ("IKEA-LG-002", 260, "7.20")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "IKEA-RCPT-2026-003-A",
                    "wh_code": "BLR-HUB",
                    "loc_code": "BLR-RCV",
                    "lines": [("IKEA-LG-001", 360), ("IKEA-LG-002", 60)],
                    "batch": True,
                    "serial": True,
                    "complete_putaway": "all",
                }
            ],
            "bill_action": "SENT",
        },
        {
            "number": "IKEA-PO-2026-004",
            "vendor": "NorthStar Textiles",
            "days_ago": 12,
            "expected_in_days": 4,
            "items": [("IKEA-TE-001", 360, "8.90")],
            "submit": True,
            "approve": True,
            "cancel": True,
        },
    ]

    out: dict[str, PurchaseOrder] = {}
    for plan in plans:
        existing_po = purchase_order_by_number(db, tenant_id, plan["number"])
        if existing_po is None:
            po = purchasing.create_purchase_order(
                tenant_id,
                purchase_user.id,
                {
                    "vendor_id": vendors[plan["vendor"]],
                    "po_number": plan["number"],
                    "order_date": today - timedelta(days=plan["days_ago"]),
                    "expected_date": max(today - timedelta(days=plan["days_ago"]), today, today + timedelta(days=plan["expected_in_days"])),
                    "notes": f"{SEED_TAG} IKEA procurement seed",
                    "items": [
                        {
                            "product_id": products_by_sku[sku].id,
                            "ordered_quantity": as_decimal(qty),
                            "unit_cost": as_decimal(unit_cost),
                            "notes": f"{SEED_TAG} line",
                        }
                        for sku, qty, unit_cost in plan["items"]
                    ],
                },
            )
        else:
            po = purchasing.get_purchase_order(tenant_id, existing_po.id)

        if plan.get("submit") and po.status == po.status.DRAFT:
            po = purchasing.submit_purchase_order(tenant_id, purchase_user.id, po.id)
        if plan.get("approve") and po.status == po.status.SUBMITTED:
            po = purchasing.approve_purchase_order(tenant_id, po.id, admin_user.id)
        if plan.get("cancel") and po.status in (po.status.DRAFT, po.status.SUBMITTED):
            po = purchasing.cancel_purchase_order(tenant_id, po.id)

        for receipt_plan in plan.get("receipts", []):
            existing_receipt = receipt_by_number(db, tenant_id, receipt_plan["number"])
            if existing_receipt is None:
                refreshed_po = purchasing.get_purchase_order(tenant_id, po.id)
                po_item_by_product = {item.product_id: item for item in refreshed_po.items}
                wh = warehouses[receipt_plan["wh_code"]]
                loc_id = wh["locations"][receipt_plan["loc_code"]]
                receipt_items = []
                for sku, qty in receipt_plan["lines"]:
                    product = products_by_sku[sku]
                    item_payload: dict[str, Any] = {
                        "purchase_order_item_id": po_item_by_product[product.id].id,
                        "product_id": product.id,
                        "warehouse_id": wh["id"],
                        "location_id": loc_id,
                        "received_quantity": as_decimal(qty),
                    }
                    if receipt_plan.get("batch") and (product.track_batch or product.track_expiry):
                        item_payload.update(
                            {
                                "batch_number": f"{plan['number']}-{sku}-B1",
                                "supplier_batch_number": f"SUP-{sku[-3:]}",
                                "manufacture_date": today - timedelta(days=45),
                                "expiry_date": today + timedelta(days=365),
                                "warranty_until": today + timedelta(days=540),
                            }
                        )
                    if receipt_plan.get("serial") and product.track_serial:
                        item_payload["serial_numbers"] = [f"{sku}-SN-{index:04d}" for index in range(1, int(qty) + 1)]
                    receipt_items.append(item_payload)
                receipt = purchasing.create_receipt(
                    tenant_id,
                    inventory_user.id,
                    po.id,
                    {
                        "receipt_number": receipt_plan["number"],
                        "received_at": datetime.now(UTC),
                        "notes": f"{SEED_TAG} receipt for {plan['number']}",
                        "items": receipt_items,
                    },
                )
            else:
                receipt = purchasing.get_receipt(tenant_id, existing_receipt.id)

            if receipt.status == receipt.status.DRAFT:
                purchasing.commit_receipt(
                    tenant_id,
                    inventory_user.id,
                    receipt.id,
                    {"idempotency_key": f"{SEED_TAG}:{receipt_plan['number']}:commit", "note": f"{SEED_TAG} commit"},
                )
                receipt = purchasing.get_receipt(tenant_id, receipt.id)

            complete_putaway = receipt_plan.get("complete_putaway")
            if complete_putaway:
                base_seed.complete_putaway_for_receipt(db, tenant_id, receipt.id, inventory_user.id, None if complete_putaway == "all" else int(complete_putaway))

        bill_action = plan.get("bill_action")
        if bill_action:
            bill = db.query(Bill).filter(Bill.tenant_id == tenant_id, Bill.purchase_order_id == po.id).first()
            if bill is None:
                try:
                    bill = docs.create_bill(
                        tenant_id,
                        purchase_user.id,
                        {
                            "purchase_order_id": po.id,
                            "issue_date": today - timedelta(days=2),
                            "due_date": today + timedelta(days=21),
                            "notes": f"{SEED_TAG} bill for {plan['number']}",
                        },
                    )
                except Exception:
                    bill = None
            if bill is not None and bill.status == bill.status.DRAFT and bill_action in {"SENT", "PAID"}:
                try:
                    bill = docs.send_bill(tenant_id, bill.id, purchase_user.id)
                except Exception:
                    bill = docs.get_bill(tenant_id, bill.id)
            if bill is not None and bill_action == "PAID":
                fresh = docs.get_bill(tenant_id, bill.id)
                if fresh.status != fresh.status.PAID:
                    docs.mark_bill_paid(tenant_id, bill.id, purchase_user.id)

        out[plan["number"]] = purchasing.get_purchase_order(tenant_id, po.id)
    return out


def seed_sales_workflows(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    products_by_sku: dict[str, Product],
    customers: dict[str, int],
) -> dict[str, SalesOrder]:
    sales_user = users_by_role["SALES_STAFF"]
    inventory_user = users_by_role["INVENTORY_MANAGER"]
    sales = SalesService(db)
    docs = DocumentsService(db)
    fulfillment_repo = FulfillmentRepository(db)
    fulfillment_service = FulfillmentService(db)
    today = date.today()

    plans = [
        {"number": "IKEA-SO-2026-001", "customer": "IKEA Online Store", "days_ago": 18, "ship_in_days": 2, "items": [("IKEA-LV-001", 20), ("IKEA-ST-001", 18)], "state": "DRAFT"},
        {"number": "IKEA-SO-2026-002", "customer": "Scandinavian Home Retail", "days_ago": 16, "ship_in_days": 1, "items": [("IKEA-LV-002", 44), ("IKEA-DC-002", 60)], "state": "CONFIRMED"},
        {"number": "IKEA-SO-2026-003", "customer": "Nordic Living Concepts", "days_ago": 14, "ship_in_days": 1, "items": [("IKEA-LV-003", 12), ("IKEA-BD-001", 8)], "state": "PARTIALLY_FULFILLED"},
        {"number": "IKEA-SO-2026-004", "customer": "Urban Apartment Supply", "days_ago": 12, "ship_in_days": 0, "items": [("IKEA-LV-001", 16), ("IKEA-DC-001", 45), ("IKEA-ST-002", 30)], "state": "FULFILLED_SENT_INVOICE"},
        {"number": "IKEA-SO-2026-005", "customer": "Campus Housing Group", "days_ago": 9, "ship_in_days": 2, "items": [("IKEA-DC-002", 24), ("IKEA-TE-001", 36)], "state": "FULFILLED_PAID_INVOICE"},
    ]

    out: dict[str, SalesOrder] = {}
    for plan in plans:
        existing_so = sales_order_by_number(db, tenant_id, plan["number"])
        if existing_so is None:
            so = sales.create_sales_order(
                tenant_id,
                sales_user.id,
                {
                    "customer_id": customers[plan["customer"]],
                    "order_number": plan["number"],
                    "order_date": today - timedelta(days=plan["days_ago"]),
                    "expected_ship_date": max(today - timedelta(days=plan["days_ago"]), today, today + timedelta(days=plan["ship_in_days"])),
                    "notes": f"{SEED_TAG} IKEA sales seed",
                    "items": [
                        {
                            "product_id": products_by_sku[sku].id,
                            "ordered_quantity": as_decimal(qty),
                            "unit_price": as_decimal(products_by_sku[sku].selling_price),
                            "notes": f"{SEED_TAG} sales line",
                        }
                        for sku, qty in plan["items"]
                    ],
                },
            )
        else:
            so = sales.get_sales_order(tenant_id, existing_so.id)

        if plan["state"] not in {"DRAFT", "CANCELLED"} and so.status == so.status.DRAFT:
            allocations = base_seed.allocations_for_order(db, tenant_id, so, split_first_item=(plan["state"] == "PARTIALLY_FULFILLED"))
            sales.confirm_sales_order(
                tenant_id,
                sales_user.id,
                so.id,
                {"idempotency_key": f"{SEED_TAG}:{plan['number']}:confirm", "note": f"{SEED_TAG} confirm", "allocations": allocations},
            )
            so = sales.get_sales_order(tenant_id, so.id)

        if plan["state"] == "PARTIALLY_FULFILLED":
            reservations = fulfillment_repo.active_reservations_for_order(tenant_id, so.order_number)
            if reservations:
                first = reservations[0]
                order_item = next((item for item in so.items if item.product_id == first.product_id), None)
                if order_item is not None:
                    fulfillment = sales.create_fulfillment(
                        tenant_id,
                        inventory_user.id,
                        so.id,
                        {
                            "fulfillment_number": f"{SEED_TAG}-FUL-{plan['number']}-P1",
                            "notes": f"{SEED_TAG} partial fulfillment",
                            "items": [
                                {
                                    "sales_order_item_id": order_item.id,
                                    "product_id": first.product_id,
                                    "warehouse_id": first.warehouse_id,
                                    "location_id": first.location_id,
                                    "reservation_id": first.id,
                                    "fulfilled_quantity": first.quantity,
                                }
                            ],
                        },
                    )
                    sales.commit_fulfillment(
                        tenant_id,
                        inventory_user.id,
                        fulfillment.id,
                        {"idempotency_key": f"{SEED_TAG}:{plan['number']}:partial-commit", "note": f"{SEED_TAG} partial commit"},
                    )
                so = sales.get_sales_order(tenant_id, so.id)
        else:
            open_pick_tasks = (
                db.query(PickTask)
                .filter(
                    PickTask.tenant_id == tenant_id,
                    PickTask.sales_order_id == so.id,
                    PickTask.status.in_([PickTaskStatus.PENDING, PickTaskStatus.IN_PROGRESS]),
                )
                .order_by(PickTask.id.asc())
                .all()
            )
            for pick_task in open_pick_tasks:
                payload = {
                    "items": [
                        {"pick_task_item_id": pick_item.id, "picked_quantity": str(pick_item.required_quantity)}
                        for pick_item in pick_task.items
                    ]
                }
                fulfillment_service.pick_pick_task(tenant_id, inventory_user.id, pick_task.id, payload)
            so = sales.get_sales_order(tenant_id, so.id)

        if plan["state"] in {"FULFILLED_SENT_INVOICE", "FULFILLED_PAID_INVOICE"}:
            invoice = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.sales_order_id == so.id).first()
            if invoice is None:
                try:
                    invoice = docs.create_invoice(
                        tenant_id,
                        sales_user.id,
                        {
                            "sales_order_id": so.id,
                            "issue_date": today - timedelta(days=1),
                            "due_date": today + timedelta(days=14),
                            "notes": f"{SEED_TAG} invoice for {plan['number']}",
                        },
                    )
                except Exception:
                    invoice = None
            if invoice is not None and invoice.status == invoice.status.DRAFT:
                try:
                    invoice = docs.send_invoice(tenant_id, invoice.id, sales_user.id)
                except Exception:
                    invoice = docs.get_invoice(tenant_id, invoice.id)
            if plan["state"] == "FULFILLED_PAID_INVOICE" and invoice is not None:
                fresh = docs.get_invoice(tenant_id, invoice.id)
                if fresh.status != fresh.status.PAID:
                    docs.mark_invoice_paid(tenant_id, invoice.id, sales_user.id)

        out[plan["number"]] = sales.get_sales_order(tenant_id, so.id)
    return out


def seed_return_workflows(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    sales_orders: dict[str, SalesOrder],
    warehouses: dict[str, dict[str, Any]],
) -> dict[str, SalesReturn]:
    sales_user = users_by_role["SALES_STAFF"]
    inventory_user = users_by_role["INVENTORY_MANAGER"]
    returns_service = ReturnsService(db)
    ret_wh = warehouses["STH-DC"]["id"]
    ret_loc = warehouses["STH-DC"]["locations"]["STH-RET"]

    plans = [
        {"number": "IKEA-RET-2026-001", "order": "IKEA-SO-2026-004", "state": "SUBMITTED", "qc": "RESTOCK"},
        {"number": "IKEA-RET-2026-002", "order": "IKEA-SO-2026-005", "state": "PROCESSED", "qc": "MIXED"},
        {"number": "IKEA-RET-2026-003", "order": "IKEA-SO-2026-003", "state": "CANCELLED", "qc": None},
    ]

    out: dict[str, SalesReturn] = {}
    for plan in plans:
        source_order = sales_orders[plan["order"]]
        existing = return_by_number(db, tenant_id, plan["number"])
        if existing is None:
            source_item = next((item for item in source_order.items if as_decimal(item.fulfilled_quantity) > 0), None)
            if source_item is None:
                continue
            qty = min(as_decimal(source_item.fulfilled_quantity), Decimal("2"))
            created = returns_service.create_return(
                tenant_id,
                sales_user.id,
                {
                    "sales_order_id": source_order.id,
                    "return_number": plan["number"],
                    "reason": "Customer changed mind after assembly",
                    "notes": f"{SEED_TAG} return seed",
                    "items": [
                        {
                            "sales_order_item_id": source_item.id,
                            "warehouse_id": ret_wh,
                            "location_id": ret_loc,
                            "returned_quantity": qty,
                            "reason": "Packaging opened during delivery",
                            "notes": f"{SEED_TAG} intake",
                        }
                    ],
                },
            )
            sales_return = returns_service.get_return(tenant_id, created.id)
        else:
            sales_return = returns_service.get_return(tenant_id, existing.id)

        if plan["state"] in {"SUBMITTED", "PROCESSED"} and sales_return.status == sales_return.status.DRAFT:
            sales_return = returns_service.submit_return(tenant_id, sales_user.id, sales_return.id)
        if plan["state"] == "CANCELLED" and sales_return.status in (sales_return.status.DRAFT, sales_return.status.SUBMITTED, sales_return.status.INSPECTION_PENDING):
            sales_return = returns_service.cancel_return(tenant_id, sales_return.id)
        if plan["state"] in {"SUBMITTED", "PROCESSED"} and sales_return.status in (sales_return.status.SUBMITTED, sales_return.status.INSPECTION_PENDING):
            inspection_items = []
            for item in sales_return.items:
                if plan["qc"] == "RESTOCK":
                    inspection_items.append(
                        {
                            "sales_return_item_id": item.id,
                            "qc_status": SalesReturnItemStatus.ACCEPTED_RESTOCK,
                            "accepted_quantity": item.returned_quantity,
                            "rejected_quantity": Decimal("0"),
                            "reason": "Resalable stock",
                            "notes": f"{SEED_TAG} qc restock",
                        }
                    )
                else:
                    accepted = min(as_decimal(item.returned_quantity), Decimal("1"))
                    rejected = as_decimal(item.returned_quantity) - accepted
                    inspection_items.append(
                        {
                            "sales_return_item_id": item.id,
                            "qc_status": SalesReturnItemStatus.ACCEPTED_BLOCKED if rejected == 0 else SalesReturnItemStatus.DAMAGED,
                            "accepted_quantity": accepted,
                            "rejected_quantity": rejected,
                            "reason": "Mixed quality return",
                            "notes": f"{SEED_TAG} qc mixed",
                        }
                    )
            sales_return = returns_service.inspect_return(
                tenant_id,
                inventory_user.id,
                sales_return.id,
                {"notes": f"{SEED_TAG} inspection", "items": inspection_items},
            )
        if plan["state"] == "PROCESSED" and sales_return.status == sales_return.status.INSPECTION_PENDING:
            returns_service.process_return(
                tenant_id,
                inventory_user.id,
                sales_return.id,
                {"idempotency_key": f"{SEED_TAG}:{plan['number']}:process", "note": f"{SEED_TAG} process"},
            )
            sales_return = returns_service.get_return(tenant_id, sales_return.id)
        out[plan["number"]] = sales_return
    return out


def seed_cycle_count_workflows(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    products_by_sku: dict[str, Product],
    warehouses: dict[str, dict[str, Any]],
) -> list[StockCountSession]:
    inventory_user = users_by_role["INVENTORY_MANAGER"]
    cycle_service = CycleCountService(db)
    sessions: list[StockCountSession] = []

    plans = [
        {
            "key": "IKEA-CC-2026-001",
            "warehouse_code": "STH-DC",
            "state": "SUBMITTED",
            "lines": [("IKEA-LV-001", "STH-STR", Decimal("418")), ("IKEA-LG-001", "STH-STR", Decimal("355"))],
        },
        {
            "key": "IKEA-CC-2026-002",
            "warehouse_code": "BLR-HUB",
            "state": "RECONCILED",
            "lines": [("IKEA-LG-002", "BLR-STR", Decimal("178")), ("IKEA-DC-001", "BLR-STR", Decimal("258"))],
        },
    ]

    for plan in plans:
        warehouse_id = warehouses[plan["warehouse_code"]]["id"]
        existing = (
            db.query(StockCountSession)
            .filter(
                StockCountSession.tenant_id == tenant_id,
                StockCountSession.warehouse_id == warehouse_id,
                StockCountSession.notes == f"{SEED_TAG} {plan['key']}",
            )
            .first()
        )
        if existing is None:
            session = cycle_service.create_session(tenant_id, inventory_user.id, {"warehouse_id": warehouse_id, "notes": f"{SEED_TAG} {plan['key']}"})
        else:
            session = cycle_service.get_session(tenant_id, existing.id)

        existing_lines = {(line.product_id, line.location_id): line for line in cycle_service.list_lines(tenant_id, session.id)}
        for sku, loc_code, counted_qty in plan["lines"]:
            product = products_by_sku[sku]
            location_id = warehouses[plan["warehouse_code"]]["locations"][loc_code]
            line = existing_lines.get((product.id, location_id))
            if line is None:
                line = cycle_service.add_line(tenant_id, session.id, {"product_id": product.id, "location_id": location_id})
            if line.counted_quantity is None or as_decimal(line.counted_quantity) != as_decimal(counted_qty):
                cycle_service.update_line(tenant_id, session.id, line.id, {"counted_quantity": counted_qty, "notes": f"{SEED_TAG} counted"})

        session = cycle_service.get_session(tenant_id, session.id)
        if plan["state"] == "SUBMITTED" and session.status in (session.status.DRAFT, session.status.IN_PROGRESS):
            session = cycle_service.submit(tenant_id, session.id)
        if plan["state"] == "RECONCILED" and session.status == session.status.SUBMITTED:
            session, _ = cycle_service.reconcile(tenant_id, session.id, inventory_user.id)
        sessions.append(cycle_service.get_session(tenant_id, session.id))
    return sessions


def seed_workflow_history(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    vendors: dict[str, int],
    customers: dict[str, int],
    products: dict[str, int],
    warehouses: dict[str, dict[str, Any]],
) -> dict[str, int]:
    products_by_sku = load_products(db, tenant_id)
    purchase_orders = seed_purchase_workflows(db, tenant_id, users_by_role, products_by_sku, vendors, warehouses)
    sales_orders = seed_sales_workflows(db, tenant_id, users_by_role, products_by_sku, customers)
    returns = seed_return_workflows(db, tenant_id, users_by_role, sales_orders, warehouses)
    cycle_sessions = seed_cycle_count_workflows(db, tenant_id, users_by_role, products_by_sku, warehouses)
    return {
        "purchase_orders_seeded": len(purchase_orders),
        "sales_orders_seeded": len(sales_orders),
        "returns_seeded": len(returns),
        "cycle_sessions_seeded": len(cycle_sessions),
    }


def summarize_counts(db: Session, tenant_id: int) -> dict[str, int]:
    return {
        "users": db.query(User).filter(User.tenant_id == tenant_id).count(),
        "categories": db.query(Category).filter(Category.tenant_id == tenant_id).count(),
        "brands": db.query(Brand).filter(Brand.tenant_id == tenant_id).count(),
        "vendors": db.query(Vendor).filter(Vendor.tenant_id == tenant_id).count(),
        "customers": db.query(Customer).filter(Customer.tenant_id == tenant_id).count(),
        "products": db.query(Product).filter(Product.tenant_id == tenant_id).count(),
        "warehouses": db.query(Warehouse).filter(Warehouse.tenant_id == tenant_id).count(),
        "warehouse_locations": db.query(WarehouseLocation).filter(WarehouseLocation.tenant_id == tenant_id).count(),
        "reorder_rules": db.query(ReorderRule).filter(ReorderRule.tenant_id == tenant_id).count(),
        "purchase_orders": db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id).count(),
        "purchase_receipts": db.query(PurchaseReceipt).filter(PurchaseReceipt.tenant_id == tenant_id).count(),
        "putaway_tasks": db.query(PutawayTask).filter(PutawayTask.tenant_id == tenant_id).count(),
        "sales_orders": db.query(SalesOrder).filter(SalesOrder.tenant_id == tenant_id).count(),
        "pick_tasks": db.query(PickTask).filter(PickTask.tenant_id == tenant_id).count(),
        "sales_fulfillments": db.query(SalesFulfillment).filter(SalesFulfillment.tenant_id == tenant_id).count(),
        "sales_returns": db.query(SalesReturn).filter(SalesReturn.tenant_id == tenant_id).count(),
        "invoices": db.query(Invoice).filter(Invoice.tenant_id == tenant_id).count(),
        "bills": db.query(Bill).filter(Bill.tenant_id == tenant_id).count(),
        "stock_count_sessions": db.query(StockCountSession).filter(StockCountSession.tenant_id == tenant_id).count(),
        "workflow_events": db.query(WorkflowEvent).filter(WorkflowEvent.tenant_id == tenant_id).count(),
        "workflow_tasks": db.query(WorkflowTask).filter(WorkflowTask.tenant_id == tenant_id).count(),
        "warehouse_stock": db.query(WarehouseStock).filter(WarehouseStock.tenant_id == tenant_id).count(),
    }


def main() -> None:
    upgrade_database()
    db = SessionLocal()
    try:
        tenant, admin = upsert_tenant_and_admin(db)
        print(f"Seeding data for tenant: {tenant.company_name} (ID: {tenant.id})")

        categories = seed_categories(db, tenant.id)
        brands = seed_brands(db, tenant.id)
        vendors = seed_vendors(db, tenant.id)
        customers = seed_customers(db, tenant.id)
        products = seed_products(db, tenant.id, categories, brands)
        warehouses = seed_warehouses(db, tenant.id)
        seed_reorder_rules(db, tenant.id, products, warehouses)
        db.commit()

        stocked = seed_stock(db, tenant.id, admin.id, products, warehouses)
        users_by_role = ensure_role_users(db, tenant.id)
        users_by_role["TENANT_ADMIN"] = admin
        workflow_summary = seed_workflow_history(db, tenant.id, users_by_role, vendors, customers, products, warehouses)

        counts = summarize_counts(db, tenant.id)

        print("\nSeed complete!")
        print(f"  Tenant: {tenant.company_name}")
        print("  Admin: admin@ikea.com")
        print("  Shared password for all IKEA users: Ikea@12345")
        print(f"  Seeded stock entries: {stocked}")
        print(f"  Purchase workflows: {workflow_summary['purchase_orders_seeded']}")
        print(f"  Sales workflows: {workflow_summary['sales_orders_seeded']}")
        print(f"  Return workflows: {workflow_summary['returns_seeded']}")
        print(f"  Cycle count workflows: {workflow_summary['cycle_sessions_seeded']}")
        print("\n  Table totals:")
        for key, value in counts.items():
            print(f"    - {key}: {value}")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
