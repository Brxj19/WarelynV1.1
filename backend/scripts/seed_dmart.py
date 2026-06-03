"""Seed a complete D-Mart wholesale tenant with realistic workflow data.

Run from backend/:
    .venv/bin/python scripts/seed_dmart.py

The script is idempotent for the D-Mart tenant:
- it leaves the existing database untouched if the tenant already exists
- it exits successfully when SEED_ON_STARTUP=false
- it keeps existing data intact when rerun
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.communication import NotificationCategory, NotificationPriority, NotificationType
from app.models.inventory import ReferenceType
from app.models.master_data import Category, Customer, LocationType, Product, RecordStatus, Vendor, Warehouse, WarehouseLocation
from app.models.operations import ReorderRule
from app.models.communication import Notification
from app.models.purchasing import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, PurchaseReceipt, PurchaseReceiptItem, PurchaseReceiptStatus
from app.models.returns import SalesReturn, SalesReturnItem, SalesReturnItemStatus, SalesReturnStatus
from app.models.sales import SalesOrder, SalesOrderItem, SalesOrderStatus
from app.models.settings import TenantSettings
from app.models.workflow import WorkflowTask, WorkflowTaskPriority, WorkflowTaskStatus
from app.models.inventory import InventoryBatch, InventorySerial
from app.models.documents import Invoice
from app.repositories.fulfillment import FulfillmentRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.sales import SalesRepository
from app.repositories.settings import TenantSettingsRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.fulfillment import FulfillmentService
from app.services.inventory import InventoryService
from app.services.notification import NotificationService
from app.services.returns import ReturnsService
from app.services.sales import SalesService
from app.services.workflow import WorkflowService

SEED_TAG = "DMART-SEED-2026Q2"
SUPER_ADMIN_EMAIL = "superadmin@warelyn.dev"
SUPER_ADMIN_PASSWORD = "Admin@1234"
SUPER_ADMIN_NAME = "Warelyn Super Admin"

TENANT_NAME = "D-Mart Wholesale Pvt Ltd"
TENANT_CONTACT_EMAIL = "admin@dmart.in"
TENANT_PHONE = "+91-22-5555-0001"
TENANT_ADDRESS = "Plot 14, APMC Market, Navi Mumbai, Maharashtra 400703"
TENANT_PASSWORD = "Admin@1234"

DMART_WAREHOUSE_NAME = "D-Mart Central Warehouse"
DMART_WAREHOUSE_CODE = "DMART-MAIN"

BASE_NOW = datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC)


def d(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value))


def dt(year: int, month: int, day: int) -> date:
    return date(year, month, day)


@dataclass(frozen=True)
class ReceiptPlan:
    sku: str
    sku_fragment: str
    category_code: str
    product_name: str
    vendor_name: str
    tracking: str
    receipt_index: int
    po_number: str
    receipt_number: str
    quantity: int
    location_code: str
    batch_number: str | None = None
    supplier_batch_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    serial_numbers: tuple[str, ...] = ()


PRODUCT_SPECS: list[dict[str, Any]] = [
    {
        "category_name": "Electronics",
        "category_code": "ELEC",
        "vendor_name": "Samsung India Electronics Pvt Ltd",
        "name": "Samsung 43-inch Smart TV",
        "sku": "ELEC-TV-SAM43",
        "sku_fragment": "SAMTV43",
        "tracking": "SERIAL",
        "unit": "Piece",
        "cost_price": d("18500.00"),
        "selling_price": d("22999.00"),
        "reorder_level": 10,
        "barcode": "890700000001",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("ELECTRONICS-SHELF-1", "ELECTRONICS-SHELF-2", "ELECTRONICS-SHELF-1"),
    },
    {
        "category_name": "Electronics",
        "category_code": "ELEC",
        "vendor_name": "Samsung India Electronics Pvt Ltd",
        "name": "boAt Rockerz 450 Bluetooth Headphones",
        "sku": "ELEC-HP-BOAT450",
        "sku_fragment": "BOAT450",
        "tracking": "SERIAL",
        "unit": "Piece",
        "cost_price": d("850.00"),
        "selling_price": d("1299.00"),
        "reorder_level": 20,
        "barcode": "890700000002",
        "receipt_quantities": (35, 30, 25),
        "receipt_locations": ("ELECTRONICS-SHELF-2", "ELECTRONICS-SHELF-1", "ELECTRONICS-SHELF-2"),
    },
    {
        "category_name": "Food & Grocery",
        "category_code": "FOOD",
        "vendor_name": "Hindustan Unilever Limited",
        "name": "Aashirvaad Atta 10kg",
        "sku": "FOOD-ATTA-ASH10",
        "sku_fragment": "ATTA",
        "tracking": "BATCH",
        "unit": "Bag",
        "cost_price": d("320.00"),
        "selling_price": d("385.00"),
        "reorder_level": 25,
        "barcode": "890700000003",
        "receipt_quantities": (200, 170, 150),
        "receipt_locations": ("COLD-STORE-1", "COLD-STORE-2", "COLD-STORE-1"),
        "receipt_mfg_dates": (dt(2024, 11, 15), dt(2025, 5, 10), dt(2025, 11, 5)),
        "receipt_expiry_dates": (dt(2025, 11, 15), dt(2026, 5, 10), dt(2026, 11, 5)),
    },
    {
        "category_name": "Food & Grocery",
        "category_code": "FOOD",
        "vendor_name": "Hindustan Unilever Limited",
        "name": "Amul Full Cream Milk 1L Tetra Pack",
        "sku": "FOOD-MILK-AMUL1L",
        "sku_fragment": "MILK",
        "tracking": "BATCH",
        "unit": "Litre",
        "cost_price": d("62.00"),
        "selling_price": d("75.00"),
        "reorder_level": 30,
        "barcode": "890700000004",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("COLD-STORE-1", "COLD-STORE-2", "COLD-STORE-1"),
        "receipt_mfg_dates": (dt(2025, 1, 5), dt(2025, 2, 1), dt(2025, 2, 20)),
        "receipt_expiry_dates": (dt(2025, 1, 25), dt(2025, 2, 20), dt(2025, 3, 12)),
    },
    {
        "category_name": "Cosmetics",
        "category_code": "COSM",
        "vendor_name": "Nykaa Cosmetics Pvt Ltd",
        "name": "Lakme Sun Expert SPF 50 Sunscreen 100ml",
        "sku": "COS-SUN-LAK100",
        "sku_fragment": "LAK100",
        "tracking": "BATCH",
        "unit": "Bottle",
        "cost_price": d("145.00"),
        "selling_price": d("215.00"),
        "reorder_level": 20,
        "barcode": "890700000005",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("RACK-A1", "RACK-A2", "RACK-A1"),
        "receipt_mfg_dates": (dt(2024, 7, 1), dt(2025, 1, 12), dt(2025, 8, 20)),
        "receipt_expiry_dates": (dt(2026, 7, 1), dt(2027, 1, 12), dt(2027, 8, 20)),
    },
    {
        "category_name": "Cosmetics",
        "category_code": "COSM",
        "vendor_name": "Nykaa Cosmetics Pvt Ltd",
        "name": "L'Oreal Paris Total Repair 5 Shampoo 340ml",
        "sku": "COS-SHP-LOR340",
        "sku_fragment": "LOR340",
        "tracking": "BATCH",
        "unit": "Bottle",
        "cost_price": d("210.00"),
        "selling_price": d("310.00"),
        "reorder_level": 15,
        "barcode": "890700000006",
        "receipt_quantities": (25, 20, 15),
        "receipt_locations": ("RACK-A2", "RACK-A3", "RACK-A2"),
        "receipt_mfg_dates": (dt(2024, 4, 1), dt(2025, 2, 1), dt(2025, 8, 15)),
        "receipt_expiry_dates": (dt(2026, 10, 1), dt(2027, 8, 1), dt(2028, 2, 15)),
    },
    {
        "category_name": "Clothing",
        "category_code": "CLO",
        "vendor_name": "Raymond Apparel Ltd",
        "name": "Raymond Pure Wool Suit Fabric 3m",
        "sku": "CLO-SUIT-RAY3M",
        "sku_fragment": "RAY3M",
        "tracking": "STANDARD",
        "unit": "Metre",
        "cost_price": d("1800.00"),
        "selling_price": d("2699.00"),
        "reorder_level": 15,
        "barcode": "890700000007",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("FASHION-RACK-1", "FASHION-RACK-2", "FASHION-RACK-1"),
    },
    {
        "category_name": "Clothing",
        "category_code": "CLO",
        "vendor_name": "Raymond Apparel Ltd",
        "name": "Jockey Cotton Briefs Pack of 3",
        "sku": "CLO-UND-JOC3P",
        "sku_fragment": "JOC3P",
        "tracking": "STANDARD",
        "unit": "Pack",
        "cost_price": d("220.00"),
        "selling_price": d("349.00"),
        "reorder_level": 25,
        "barcode": "890700000008",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("FASHION-RACK-2", "FASHION-RACK-1", "FASHION-RACK-2"),
    },
    {
        "category_name": "Stationery",
        "category_code": "STAT",
        "vendor_name": "Classmate Stationery (ITC Ltd)",
        "name": "Classmate A4 Ruled Notebook 200 Pages",
        "sku": "STA-NB-CLS200",
        "sku_fragment": "CLS200",
        "tracking": "STANDARD",
        "unit": "Piece",
        "cost_price": d("42.00"),
        "selling_price": d("65.00"),
        "reorder_level": 30,
        "barcode": "890700000009",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("STATIONERY-SHELF-1", "STATIONERY-SHELF-1", "RACK-B1"),
    },
    {
        "category_name": "Stationery",
        "category_code": "STAT",
        "vendor_name": "Classmate Stationery (ITC Ltd)",
        "name": "Reynolds 045 Ball Pen Blue Box of 50",
        "sku": "STA-PEN-REY50",
        "sku_fragment": "REY50",
        "tracking": "STANDARD",
        "unit": "Box",
        "cost_price": d("145.00"),
        "selling_price": d("210.00"),
        "reorder_level": 20,
        "barcode": "890700000010",
        "receipt_quantities": (250, 200, 150),
        "receipt_locations": ("STATIONERY-SHELF-1", "STATIONERY-SHELF-1", "STATIONERY-SHELF-1"),
    },
    {
        "category_name": "Health & Wellness",
        "category_code": "HEAL",
        "vendor_name": "Dabur India Ltd",
        "name": "Dabur Chyawanprash 1kg",
        "sku": "HW-CHY-DAB1KG",
        "sku_fragment": "DAB1KG",
        "tracking": "BATCH",
        "unit": "Jar",
        "cost_price": d("195.00"),
        "selling_price": d("285.00"),
        "reorder_level": 20,
        "barcode": "890700000011",
        "receipt_quantities": (30, 25, 20),
        "receipt_locations": ("RACK-B1", "RACK-B2", "RACK-B1"),
        "receipt_mfg_dates": (dt(2024, 8, 1), dt(2025, 3, 1), dt(2025, 10, 1)),
        "receipt_expiry_dates": (dt(2026, 8, 1), dt(2027, 3, 1), dt(2027, 10, 1)),
    },
    {
        "category_name": "Health & Wellness",
        "category_code": "HEAL",
        "vendor_name": "Dabur India Ltd",
        "name": "Himalaya Liv.52 Tablets 100 Count",
        "sku": "HW-LIV-HIM100",
        "sku_fragment": "HIM100",
        "tracking": "BATCH",
        "unit": "Strip",
        "cost_price": d("88.00"),
        "selling_price": d("135.00"),
        "reorder_level": 25,
        "barcode": "890700000012",
        "receipt_quantities": (25, 20, 15),
        "receipt_locations": ("RACK-B2", "RACK-B3", "RACK-B2"),
        "receipt_mfg_dates": (dt(2024, 3, 1), dt(2024, 9, 1), dt(2025, 2, 1)),
        "receipt_expiry_dates": (dt(2027, 3, 1), dt(2027, 9, 1), dt(2028, 2, 1)),
    },
]

TENANT_USERS = {
    UserRole.TENANT_ADMIN: {"name": "Rajesh Sharma", "email": "rajesh@dmart.in"},
    UserRole.INVENTORY_MANAGER: {"name": "Priya Nair", "email": "priya@dmart.in"},
    UserRole.SALES_STAFF: {"name": "Arjun Mehta", "email": "arjun@dmart.in"},
    UserRole.PURCHASE_STAFF: {"name": "Sneha Patel", "email": "sneha@dmart.in"},
    UserRole.VIEWER: {"name": "Vishal Gupta", "email": "vishal@dmart.in"},
}

CUSTOMERS = [
    {"name": "BigBasket Retail Pvt Ltd", "email": "procurement@bigbasket.com", "phone": "+91-80-1234-5001", "address": "Bengaluru, Karnataka", "gst_number": "29AABCB1234Q1Z5"},
    {"name": "Reliance Smart Superstore", "email": "vendor@reliancesmart.in", "phone": "+91-22-1234-5002", "address": "Navi Mumbai, Maharashtra", "gst_number": "27AABCR5678R1Z1"},
    {"name": "More Supermarket", "email": "buying@moreretail.in", "phone": "+91-80-1234-5003", "address": "Bengaluru, Karnataka", "gst_number": "29AABCM9012S1Z3"},
]

WAREHOUSE_LAYOUT = {
    "name": DMART_WAREHOUSE_NAME,
    "code": DMART_WAREHOUSE_CODE,
    "address": TENANT_ADDRESS,
    "locations": [
        ("RACK-A1", LocationType.STORAGE),
        ("RACK-A2", LocationType.STORAGE),
        ("RACK-A3", LocationType.STORAGE),
        ("RACK-B1", LocationType.STORAGE),
        ("RACK-B2", LocationType.STORAGE),
        ("RACK-B3", LocationType.STORAGE),
        ("COLD-STORE-1", LocationType.STORAGE),
        ("COLD-STORE-2", LocationType.STORAGE),
        ("ELECTRONICS-SHELF-1", LocationType.STORAGE),
        ("ELECTRONICS-SHELF-2", LocationType.STORAGE),
        ("FASHION-RACK-1", LocationType.STORAGE),
        ("FASHION-RACK-2", LocationType.STORAGE),
        ("STATIONERY-SHELF-1", LocationType.STORAGE),
    ],
}


def is_seed_enabled() -> bool:
    return os.getenv("SEED_ON_STARTUP", "true").lower() == "true"


def build_batch_number(category_code: str, sku_fragment: str, batch_index: int, manufacture_date: date) -> str:
    return f"{category_code}-{sku_fragment}-B{batch_index:03d}-MFG{manufacture_date:%y%m}"


def build_serial_numbers(sku_fragment: str, start_sequence: int, quantity: int, year_prefix: str = "25") -> tuple[str, ...]:
    return tuple(f"{sku_fragment}-SN-{year_prefix}{sequence:03d}" for sequence in range(start_sequence, start_sequence + quantity))


def build_receipt_plans() -> list[ReceiptPlan]:
    plans: list[ReceiptPlan] = []
    for spec in PRODUCT_SPECS:
        serial_counter = 1
        for index, quantity in enumerate(spec["receipt_quantities"], start=1):
            po_number = f"PO-DM-{spec['sku_fragment']}-{index:02d}"
            receipt_number = f"RCPT-DM-{spec['sku_fragment']}-{index:02d}"
            location_code = spec["receipt_locations"][index - 1]
            if spec["tracking"] == "SERIAL":
                serial_numbers = build_serial_numbers(spec["sku_fragment"], serial_counter, quantity)
                serial_counter += quantity
                plans.append(
                    ReceiptPlan(
                        sku=spec["sku"],
                        sku_fragment=spec["sku_fragment"],
                        category_code=spec["category_code"],
                        product_name=spec["name"],
                        vendor_name=spec["vendor_name"],
                        tracking=spec["tracking"],
                        receipt_index=index,
                        po_number=po_number,
                        receipt_number=receipt_number,
                        quantity=quantity,
                        location_code=location_code,
                        serial_numbers=serial_numbers,
                    )
                )
                continue
            if spec["tracking"] == "BATCH":
                manufacture_date = spec["receipt_mfg_dates"][index - 1]
                expiry_date = spec["receipt_expiry_dates"][index - 1]
                plans.append(
                    ReceiptPlan(
                        sku=spec["sku"],
                        sku_fragment=spec["sku_fragment"],
                        category_code=spec["category_code"],
                        product_name=spec["name"],
                        vendor_name=spec["vendor_name"],
                        tracking=spec["tracking"],
                        receipt_index=index,
                        po_number=po_number,
                        receipt_number=receipt_number,
                        quantity=quantity,
                        location_code=location_code,
                        batch_number=build_batch_number(spec["category_code"], spec["sku_fragment"], index, manufacture_date),
                        supplier_batch_number=f"SUP-{spec['sku_fragment']}-{index:02d}",
                        manufacture_date=manufacture_date,
                        expiry_date=expiry_date,
                    )
                )
                continue
            plans.append(
                ReceiptPlan(
                    sku=spec["sku"],
                    sku_fragment=spec["sku_fragment"],
                    category_code=spec["category_code"],
                    product_name=spec["name"],
                    vendor_name=spec["vendor_name"],
                    tracking=spec["tracking"],
                    receipt_index=index,
                    po_number=po_number,
                    receipt_number=receipt_number,
                    quantity=quantity,
                    location_code=location_code,
                )
            )
    return plans


def ensure_super_admin(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == SUPER_ADMIN_EMAIL))
    if user is None:
        user = User(
            tenant_id=None,
            name=SUPER_ADMIN_NAME,
            email=SUPER_ADMIN_EMAIL,
            phone="+91-90000-00000",
            password_hash=get_password_hash(SUPER_ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            email_verified_at=BASE_NOW,
        )
        db.add(user)
        db.flush()
        return user
    user.name = SUPER_ADMIN_NAME
    user.password_hash = get_password_hash(SUPER_ADMIN_PASSWORD)
    user.status = UserStatus.ACTIVE
    user.email_verified_at = user.email_verified_at or BASE_NOW
    db.flush()
    return user


def ensure_tenant(db: Session) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.company_name == TENANT_NAME))
    if tenant is None:
        tenant = Tenant(
            company_name=TENANT_NAME,
            contact_email=TENANT_CONTACT_EMAIL,
            phone=TENANT_PHONE,
            address=TENANT_ADDRESS,
            business_type="Wholesale Retail",
            status=TenantStatus.ACTIVE,
        )
        db.add(tenant)
        db.flush()
        return tenant
    tenant.contact_email = TENANT_CONTACT_EMAIL
    tenant.phone = TENANT_PHONE
    tenant.address = TENANT_ADDRESS
    tenant.business_type = "Wholesale Retail"
    tenant.status = TenantStatus.ACTIVE
    db.flush()
    return tenant


def ensure_tenant_settings(db: Session, tenant_id: int) -> TenantSettings:
    repo = TenantSettingsRepository(db)
    settings = repo.get_or_create(tenant_id)
    settings.company_display_name = TENANT_NAME
    settings.contact_email = TENANT_CONTACT_EMAIL
    settings.phone = TENANT_PHONE
    settings.address_line1 = TENANT_ADDRESS
    settings.city = "Navi Mumbai"
    settings.state = "Maharashtra"
    settings.country = "India"
    settings.postal_code = "400703"
    settings.timezone = "Asia/Kolkata"
    settings.currency = "INR"
    db.flush()
    return settings


def ensure_user(db: Session, tenant_id: int, role: UserRole, password: str) -> User:
    payload = TENANT_USERS[role]
    user = db.scalar(select(User).where(User.email == payload["email"]))
    if user is None:
        user = User(
            tenant_id=tenant_id,
            name=payload["name"],
            email=payload["email"],
            phone="+91-90000-00010",
            password_hash=get_password_hash(password),
            role=role,
            status=UserStatus.ACTIVE,
            email_verified_at=BASE_NOW,
        )
        db.add(user)
        db.flush()
        return user
    user.tenant_id = tenant_id
    user.name = payload["name"]
    user.password_hash = get_password_hash(password)
    user.role = role
    user.status = UserStatus.ACTIVE
    user.email_verified_at = user.email_verified_at or BASE_NOW
    db.flush()
    return user


def ensure_category(db: Session, tenant_id: int, name: str, description: str) -> Category:
    category = db.scalar(select(Category).where(Category.tenant_id == tenant_id, Category.name == name))
    if category is None:
        category = Category(tenant_id=tenant_id, name=name, description=description)
        db.add(category)
        db.flush()
        return category
    category.description = description
    category.status = RecordStatus.ACTIVE
    db.flush()
    return category


def ensure_vendor(db: Session, tenant_id: int, name: str, email: str, phone: str, address: str, gst_number: str) -> Vendor:
    vendor = db.scalar(select(Vendor).where(Vendor.tenant_id == tenant_id, Vendor.name == name))
    if vendor is None:
        vendor = Vendor(tenant_id=tenant_id, name=name, email=email, phone=phone, address=address, gst_number=gst_number)
        db.add(vendor)
        db.flush()
        return vendor
    vendor.email = email
    vendor.phone = phone
    vendor.address = address
    vendor.gst_number = gst_number
    vendor.status = RecordStatus.ACTIVE
    db.flush()
    return vendor


def ensure_customer(db: Session, tenant_id: int, payload: dict[str, Any]) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.tenant_id == tenant_id, Customer.email == payload["email"]))
    if customer is None:
        customer = Customer(tenant_id=tenant_id, **payload)
        db.add(customer)
        db.flush()
        return customer
    customer.name = payload["name"]
    customer.phone = payload.get("phone")
    customer.address = payload.get("address")
    customer.gst_number = payload.get("gst_number")
    customer.status = RecordStatus.ACTIVE
    db.flush()
    return customer


def ensure_warehouse(db: Session, tenant_id: int, payload: dict[str, Any]) -> Warehouse:
    warehouse = db.scalar(select(Warehouse).where(Warehouse.tenant_id == tenant_id, Warehouse.code == payload["code"]))
    if warehouse is None:
        warehouse = Warehouse(tenant_id=tenant_id, **payload)
        db.add(warehouse)
        db.flush()
        return warehouse
    warehouse.name = payload["name"]
    warehouse.address = payload.get("address")
    warehouse.status = RecordStatus.ACTIVE
    db.flush()
    return warehouse


def ensure_location(db: Session, tenant_id: int, warehouse_id: int, code: str, location_type: LocationType, sort_order: int) -> WarehouseLocation:
    location = db.scalar(
        select(WarehouseLocation).where(
            WarehouseLocation.tenant_id == tenant_id,
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.code == code,
        )
    )
    if location is None:
        location = WarehouseLocation(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            code=code,
            name=code.replace("-", " ").title(),
            location_type=location_type,
            sort_order=sort_order,
            barcode=f"{code}-BC",
        )
        db.add(location)
        db.flush()
        return location
    location.name = code.replace("-", " ").title()
    location.location_type = location_type
    location.sort_order = sort_order
    location.status = RecordStatus.ACTIVE
    db.flush()
    return location


def ensure_product(db: Session, tenant_id: int, category_id: int, payload: dict[str, Any]) -> Product:
    product = db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.sku == payload["sku"]))
    tracking = payload["tracking"]
    if product is None:
        product = Product(
            tenant_id=tenant_id,
            category_id=category_id,
            brand_id=None,
            name=payload["name"],
            sku=payload["sku"],
            barcode=payload["barcode"],
            description=payload["name"],
            unit=payload["unit"],
            cost_price=payload["cost_price"],
            selling_price=payload["selling_price"],
            reorder_level=payload["reorder_level"],
            track_batch=tracking == "BATCH",
            track_expiry=tracking == "BATCH",
            track_serial=tracking == "SERIAL",
        )
        db.add(product)
        db.flush()
        return product
    product.category_id = category_id
    product.name = payload["name"]
    product.barcode = payload["barcode"]
    product.description = payload["name"]
    product.unit = payload["unit"]
    product.cost_price = payload["cost_price"]
    product.selling_price = payload["selling_price"]
    product.reorder_level = payload["reorder_level"]
    product.track_batch = tracking == "BATCH"
    product.track_expiry = tracking == "BATCH"
    product.track_serial = tracking == "SERIAL"
    product.status = RecordStatus.ACTIVE
    db.flush()
    return product


def ensure_reorder_rule(db: Session, tenant_id: int, product_id: int, warehouse_id: int, product: Product) -> ReorderRule:
    rule = db.scalar(
        select(ReorderRule).where(
            ReorderRule.tenant_id == tenant_id,
            ReorderRule.product_id == product_id,
            ReorderRule.warehouse_id == warehouse_id,
        )
    )
    min_quantity = d(product.reorder_level or 0)
    max_quantity = d((product.reorder_level or 0) * 4)
    safety_stock = d(max(1, (product.reorder_level or 0) // 2))
    lead_time_days = 14 if product.track_serial else 10 if product.track_batch else 7
    if rule is None:
        rule = ReorderRule(
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            min_quantity=min_quantity,
            max_quantity=max_quantity,
            safety_stock=safety_stock,
            lead_time_days=lead_time_days,
            auto_create_po=False,
            is_active=True,
        )
        db.add(rule)
        db.flush()
        return rule
    rule.min_quantity = min_quantity
    rule.max_quantity = max_quantity
    rule.safety_stock = safety_stock
    rule.lead_time_days = lead_time_days
    rule.auto_create_po = False
    rule.is_active = True
    db.flush()
    return rule


def ensure_purchase_order(
    db: Session,
    tenant_id: int,
    creator_id: int,
    vendor_id: int,
    po_number: str,
    order_date: date,
    expected_date: date | None,
    status: PurchaseOrderStatus,
    notes: str | None,
) -> PurchaseOrder:
    po = db.scalar(select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.po_number == po_number))
    if po is None:
        po = PurchaseOrder(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            po_number=po_number,
            status=status,
            order_date=order_date,
            expected_date=expected_date,
            notes=notes,
            created_by=creator_id,
            submitted_at=BASE_NOW if status in {PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CLOSED} else None,
            approved_at=BASE_NOW if status in {PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CLOSED} else None,
            received_at=BASE_NOW if status in {PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CLOSED} else None,
            closed_at=BASE_NOW if status == PurchaseOrderStatus.CLOSED else None,
        )
        db.add(po)
        db.flush()
        return po
    po.vendor_id = vendor_id
    po.order_date = order_date
    po.expected_date = expected_date
    po.status = status
    po.notes = notes
    po.created_by = creator_id
    db.flush()
    return po


def ensure_purchase_order_item(db: Session, tenant_id: int, po_id: int, product_id: int, quantity: int, unit_cost: Decimal) -> PurchaseOrderItem:
    item = db.scalar(
        select(PurchaseOrderItem).where(
            PurchaseOrderItem.tenant_id == tenant_id,
            PurchaseOrderItem.purchase_order_id == po_id,
            PurchaseOrderItem.product_id == product_id,
        )
    )
    if item is None:
        item = PurchaseOrderItem(
            tenant_id=tenant_id,
            purchase_order_id=po_id,
            product_id=product_id,
            ordered_quantity=d(quantity),
            received_quantity=d(quantity),
            unit_cost=unit_cost,
        )
        db.add(item)
        db.flush()
        return item
    item.ordered_quantity = d(quantity)
    item.received_quantity = d(quantity)
    item.unit_cost = unit_cost
    db.flush()
    return item


def ensure_purchase_receipt(
    db: Session,
    tenant_id: int,
    receiver_id: int,
    po_id: int,
    receipt_number: str,
    grn_number: str,
    notes: str | None,
) -> PurchaseReceipt:
    receipt = db.scalar(select(PurchaseReceipt).where(PurchaseReceipt.tenant_id == tenant_id, PurchaseReceipt.receipt_number == receipt_number))
    if receipt is None:
        receipt = PurchaseReceipt(
            tenant_id=tenant_id,
            purchase_order_id=po_id,
            receipt_number=receipt_number,
            grn_number=grn_number,
            status=PurchaseReceiptStatus.COMMITTED,
            received_by=receiver_id,
            received_at=BASE_NOW,
            committed_at=BASE_NOW,
            notes=notes,
        )
        db.add(receipt)
        db.flush()
        return receipt
    receipt.purchase_order_id = po_id
    receipt.grn_number = grn_number
    receipt.status = PurchaseReceiptStatus.COMMITTED
    receipt.received_by = receiver_id
    receipt.received_at = receipt.received_at or BASE_NOW
    receipt.committed_at = receipt.committed_at or BASE_NOW
    receipt.notes = notes
    db.flush()
    return receipt


def ensure_purchase_receipt_item(
    db: Session,
    tenant_id: int,
    receipt_id: int,
    purchase_order_item_id: int,
    product_id: int,
    warehouse_id: int,
    location_id: int,
    plan: ReceiptPlan,
) -> PurchaseReceiptItem:
    item = db.scalar(
        select(PurchaseReceiptItem).where(
            PurchaseReceiptItem.tenant_id == tenant_id,
            PurchaseReceiptItem.purchase_receipt_id == receipt_id,
            PurchaseReceiptItem.purchase_order_item_id == purchase_order_item_id,
        )
    )
    payload = {
        "tenant_id": tenant_id,
        "purchase_receipt_id": receipt_id,
        "purchase_order_item_id": purchase_order_item_id,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "location_id": location_id,
        "received_quantity": d(plan.quantity),
        "unit_cost": next(spec["cost_price"] for spec in PRODUCT_SPECS if spec["sku"] == plan.sku),
        "batch_number": plan.batch_number,
        "supplier_batch_number": plan.supplier_batch_number,
        "manufacture_date": plan.manufacture_date,
        "expiry_date": plan.expiry_date,
        "warranty_until": None,
        "serial_numbers": list(plan.serial_numbers) if plan.serial_numbers else None,
    }
    if item is None:
        item = PurchaseReceiptItem(**payload)
        db.add(item)
        db.flush()
        return item
    for key, value in payload.items():
        setattr(item, key, value)
    db.flush()
    return item


def ensure_stock_receipt(
    db: Session,
    tenant_id: int,
    actor_id: int,
    warehouse_id: int,
    product: Product,
    vendor_id: int,
    plan: ReceiptPlan,
    location_id: int,
) -> None:
    po = ensure_purchase_order(
        db,
        tenant_id,
        actor_id,
        vendor_id,
        plan.po_number,
        order_date=date(2025, min(12, plan.receipt_index + 1), 10),
        expected_date=date(2025, min(12, plan.receipt_index + 1), 17),
        status=PurchaseOrderStatus.RECEIVED,
        notes=f"Seeded receipt #{plan.receipt_index} for {plan.product_name}.",
    )
    po_item = ensure_purchase_order_item(db, tenant_id, po.id, product.id, plan.quantity, next(spec["cost_price"] for spec in PRODUCT_SPECS if spec["sku"] == plan.sku))
    receipt = ensure_purchase_receipt(
        db,
        tenant_id,
        actor_id,
        po.id,
        plan.receipt_number,
        f"GRN-{plan.sku_fragment}-{plan.receipt_index:02d}",
        notes=f"Seeded stock for {plan.product_name}.",
    )
    ensure_purchase_receipt_item(db, tenant_id, receipt.id, po_item.id, product.id, warehouse_id, location_id, plan)
    InventoryService(db).stock_in(
        tenant_id,
        actor_id,
        {
            "product_id": product.id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
            "quantity": plan.quantity,
            "batch_number": plan.batch_number,
            "supplier_batch_number": plan.supplier_batch_number,
            "manufacture_date": plan.manufacture_date,
            "expiry_date": plan.expiry_date,
            "warranty_until": None,
            "serial_numbers": list(plan.serial_numbers) if plan.serial_numbers else None,
            "reference_type": ReferenceType.PURCHASE_RECEIPT,
            "reference_id": receipt.receipt_number,
            "note": f"Seeded receipt {receipt.receipt_number} for {plan.product_name}.",
            "idempotency_key": f"{SEED_TAG}:stock-in:{plan.receipt_number}",
        },
        auto_commit=False,
    )
    po.status = PurchaseOrderStatus.RECEIVED
    po.received_at = po.received_at or BASE_NOW
    db.commit()


def ensure_sales_order(
    db: Session,
    tenant_id: int,
    creator_id: int,
    customer_id: int,
    order_number: str,
    order_date: date,
    expected_ship_date: date,
    notes: str | None,
    items: list[dict[str, Any]],
) -> SalesOrder:
    order = db.scalar(select(SalesOrder).where(SalesOrder.tenant_id == tenant_id, SalesOrder.order_number == order_number))
    if order is None:
        order = SalesOrder(
            tenant_id=tenant_id,
            customer_id=customer_id,
            order_number=order_number,
            status=SalesOrderStatus.CONFIRMED,
            order_date=order_date,
            expected_ship_date=expected_ship_date,
            notes=notes,
            created_by=creator_id,
            confirmed_at=BASE_NOW,
        )
        db.add(order)
        db.flush()
    else:
        order.customer_id = customer_id
        order.status = SalesOrderStatus.CONFIRMED
        order.order_date = order_date
        order.expected_ship_date = expected_ship_date
        order.notes = notes
        order.created_by = creator_id
        order.confirmed_at = order.confirmed_at or BASE_NOW

    existing_items = list(order.items)
    if not existing_items:
        for item in items:
            db.add(
                SalesOrderItem(
                    tenant_id=tenant_id,
                    sales_order_id=order.id,
                    product_id=item["product_id"],
                    ordered_quantity=d(item["ordered_quantity"]),
                    reserved_quantity=d(0),
                    fulfilled_quantity=d(0),
                    unit_price=item["unit_price"],
                    notes=item.get("notes"),
                )
            )
        db.flush()
    db.commit()
    return db.scalar(select(SalesOrder).where(SalesOrder.id == order.id))  # type: ignore[return-value]


def reserve_sales_order_inventory(
    db: Session,
    tenant_id: int,
    actor_id: int,
    order: SalesOrder,
    products_by_id: dict[int, Product],
    location_by_sku: dict[str, WarehouseLocation],
) -> None:
    inventory = InventoryService(db)
    for item in order.items:
        product = products_by_id[item.product_id]
        location = location_by_sku[product.sku]
        if product.track_serial:
            for index in range(int(item.ordered_quantity)):
                inventory.reserve_stock(
                    tenant_id,
                    actor_id,
                    {
                        "product_id": product.id,
                        "warehouse_id": location.warehouse_id,
                        "location_id": location.id,
                        "quantity": "1",
                        "reference_type": ReferenceType.SALES_ORDER,
                        "reference_id": order.order_number,
                        "note": f"Seed reservation for {order.order_number}",
                        "idempotency_key": f"{SEED_TAG}:reserve:{order.order_number}:{product.sku}:{index + 1}",
                    },
                    auto_commit=False,
                )
                item.reserved_quantity += d(1)
        else:
            inventory.reserve_stock(
                tenant_id,
                actor_id,
                {
                    "product_id": product.id,
                    "warehouse_id": location.warehouse_id,
                    "location_id": location.id,
                    "quantity": str(item.ordered_quantity),
                    "reference_type": ReferenceType.SALES_ORDER,
                    "reference_id": order.order_number,
                    "note": f"Seed reservation for {order.order_number}",
                    "idempotency_key": f"{SEED_TAG}:reserve:{order.order_number}:{product.sku}",
                },
                auto_commit=False,
            )
            item.reserved_quantity += item.ordered_quantity
    db.commit()


def create_pick_task_for_order(
    db: Session,
    tenant_id: int,
    actor_id: int,
    order: SalesOrder,
) -> None:
    workflow = WorkflowService(db)
    workflow.log_event(tenant_id, "SALES_ORDER_CONFIRMED", "sales_order", order.id, actor_id, {"order_number": order.order_number})
    workflow.create_task(
        tenant_id,
        WorkflowTaskCreate(
            workflow_type="SALES",
            entity_type="sales_order",
            entity_id=order.id,
            step_key="PICK_ORDER",
            title=f"Pick order {order.order_number}",
            description=f"Sales order {order.order_number} is ready for picking.",
            assigned_role="INVENTORY_MANAGER",
            priority=WorkflowTaskPriority.NORMAL.value,
            action_url=f"/sales/{order.id}",
            metadata_json={"source": "seed_dmart"},
        ),
        created_by=actor_id,
    )
    db.commit()


def complete_first_sales_order(
    db: Session,
    tenant_id: int,
    actor_id: int,
    order: SalesOrder,
    products_by_id: dict[int, Product],
    batches_by_sku: dict[str, list[int]],
    serials_by_sku: dict[str, list[int]],
) -> None:
    fulfillment_service = FulfillmentService(db)
    picking_pool = {sku: ids.copy() for sku, ids in serials_by_sku.items()}
    pick_task = fulfillment_service.create_pick_task(
        tenant_id,
        actor_id,
        order.id,
        {"pick_number": f"PICK-{order.order_number}", "notes": "Seed pick task for first sales order."},
    )
    pick_task = fulfillment_service.get_pick_task(tenant_id, pick_task.id)
    payload_items: list[dict[str, Any]] = []
    for item in sorted(pick_task.items, key=lambda row: row.id):
        product = products_by_id[item.product_id]
        if product.track_serial:
            serial_id = picking_pool[product.sku].pop(0)
            payload = {"pick_task_item_id": item.id, "picked_quantity": "1", "serial_id": serial_id}
            payload_items.append(payload)
            continue
        payload = {"pick_task_item_id": item.id, "picked_quantity": str(item.required_quantity)}
        if product.track_batch:
            payload["batch_id"] = batches_by_sku[product.sku][0]
        payload_items.append(payload)
    fulfillment_service.pick_pick_task(
        tenant_id,
        actor_id,
        pick_task.id,
        {"items": payload_items},
    )
    package = fulfillment_service.repository.get_open_draft_package_for_order(tenant_id, order.id)
    if package is not None:
        fulfillment_service.pack_package(
            tenant_id,
            actor_id,
            package.id,
            {"notes": "Seed package packed manually after picking."},
        )
    sales_service = SalesService(db)
    fulfillment = sales_service.repository.get_open_draft_fulfillment_for_order(tenant_id, order.id)
    if fulfillment is not None:
        sales_service.commit_fulfillment(
            tenant_id,
            actor_id,
            fulfillment.id,
            {"idempotency_key": f"{SEED_TAG}:fulfillment:{order.order_number}", "note": "Seed fulfillment commit."},
        )
    db.commit()


def create_return_for_first_sales_order(
    db: Session,
    tenant_id: int,
    actor_id: int,
    order: SalesOrder,
    products_by_sku: dict[str, Product],
    locations_by_code: dict[str, WarehouseLocation],
    serials_by_sku: dict[str, list[int]],
) -> SalesReturn:
    returns_service = ReturnsService(db)
    tv_product = products_by_sku["ELEC-TV-SAM43"]
    tv_item = next(item for item in order.items if item.product_id == tv_product.id)
    location = locations_by_code["ELECTRONICS-SHELF-1"]
    return_obj = returns_service.create_return(
        tenant_id,
        actor_id,
        {
            "sales_order_id": order.id,
            "return_number": "RTN-001",
            "reason": "Customer changed mind after delivery.",
            "notes": "Seeded return for two Samsung TVs.",
            "items": [
                {
                    "sales_order_item_id": tv_item.id,
                    "product_id": tv_product.id,
                    "warehouse_id": location.warehouse_id,
                    "location_id": location.id,
                    "serial_id": serials_by_sku[tv_product.sku][0],
                    "returned_quantity": "1",
                    "reason": "Opened box return",
                },
                {
                    "sales_order_item_id": tv_item.id,
                    "product_id": tv_product.id,
                    "warehouse_id": location.warehouse_id,
                    "location_id": location.id,
                    "serial_id": serials_by_sku[tv_product.sku][1],
                    "returned_quantity": "1",
                    "reason": "Defective packaging",
                },
            ],
        },
    )
    returns_service.submit_return(tenant_id, actor_id, return_obj.id)
    db.commit()
    return returns_service.get_return(tenant_id, return_obj.id)


def seed_open_reorder_po(
    db: Session,
    tenant_id: int,
    actor_id: int,
    purchase_staff_id: int,
    vendor_id: int,
    products_by_sku: dict[str, Product],
) -> PurchaseOrder:
    po = ensure_purchase_order(
        db,
        tenant_id,
        actor_id,
        vendor_id,
        "PO-DM-SAM-OPEN",
        order_date=dt(2026, 6, 1),
        expected_date=dt(2026, 6, 15),
        status=PurchaseOrderStatus.APPROVED,
        notes="Open purchase order for low-stock planning.",
    )
    for sku, qty, unit_cost in [("ELEC-TV-SAM43", 10, d("18500.00")), ("ELEC-HP-BOAT450", 20, d("850.00"))]:
        product = products_by_sku[sku]
        ensure_purchase_order_item(db, tenant_id, po.id, product.id, qty, unit_cost)
    workflow = WorkflowService(db)
    workflow.log_event(tenant_id, "PURCHASE_ORDER_SUBMITTED", "purchase_order", po.id, actor_id, {"po_number": po.po_number})
    workflow.create_task(
        tenant_id,
        WorkflowTaskCreate(
            workflow_type="PURCHASE",
            entity_type="purchase_order",
            entity_id=po.id,
            step_key="REORDER_STOCK",
            title=f"Review low stock for {po.po_number}",
            description="Low stock planning order awaiting purchase review.",
            assigned_role="PURCHASE_STAFF",
            priority=WorkflowTaskPriority.HIGH.value,
            action_url="/purchases",
            metadata_json={"source": "seed_dmart"},
        ),
        created_by=purchase_staff_id,
    )
    NotificationService(db).notify_role(
        tenant_id,
        "PURCHASE_STAFF",
        title="Low stock: Samsung 43-inch Smart TV",
        message="Stock level is below reorder planning threshold. Create a replenishment PO.",
        type=NotificationType.WARNING.value,
        category=NotificationCategory.INVENTORY.value,
        priority=NotificationPriority.HIGH.value,
        entity_type="product",
        entity_id=str(products_by_sku["ELEC-TV-SAM43"].id),
        action_url="/purchases/new",
    )
    db.commit()
    return po


def seed_database(db: Session) -> dict[str, int]:
    existing_seed = db.scalar(select(Tenant).where(Tenant.company_name == TENANT_NAME))
    if existing_seed is not None:
        print(f"D-Mart tenant already exists (tenant_id={existing_seed.id}); skipping seed.")
        return {"skipped": 1}

    super_admin = ensure_super_admin(db)
    tenant = ensure_tenant(db)
    ensure_tenant_settings(db, tenant.id)

    users = {role: ensure_user(db, tenant.id, role, TENANT_PASSWORD) for role in [UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF, UserRole.PURCHASE_STAFF, UserRole.VIEWER]}

    categories_by_name: dict[str, Category] = {}
    vendors_by_name: dict[str, Vendor] = {}
    customers_by_email: dict[str, Customer] = {}
    for spec in PRODUCT_SPECS:
        categories_by_name.setdefault(spec["category_name"], ensure_category(db, tenant.id, spec["category_name"], f"{spec['category_name']} products for the D-Mart tenant."))
        vendors_by_name.setdefault(
            spec["vendor_name"],
            ensure_vendor(
                db,
                tenant.id,
                spec["vendor_name"],
                {
                    "Samsung India Electronics Pvt Ltd": "procurement@samsung.in",
                    "Hindustan Unilever Limited": "orders@hul.in",
                    "Nykaa Cosmetics Pvt Ltd": "b2b@nykaa.in",
                    "Raymond Apparel Ltd": "wholesale@raymond.in",
                    "Classmate Stationery (ITC Ltd)": "trade@itc.in",
                    "Dabur India Ltd": "supply@dabur.in",
                }[spec["vendor_name"]],
                {
                    "Samsung India Electronics Pvt Ltd": "+91-22-4000-1001",
                    "Hindustan Unilever Limited": "+91-22-4000-1002",
                    "Nykaa Cosmetics Pvt Ltd": "+91-22-4000-1003",
                    "Raymond Apparel Ltd": "+91-22-4000-1004",
                    "Classmate Stationery (ITC Ltd)": "+91-22-4000-1005",
                    "Dabur India Ltd": "+91-22-4000-1006",
                }[spec["vendor_name"]],
                {
                    "Samsung India Electronics Pvt Ltd": "Bengaluru, Karnataka",
                    "Hindustan Unilever Limited": "Mumbai, Maharashtra",
                    "Nykaa Cosmetics Pvt Ltd": "Mumbai, Maharashtra",
                    "Raymond Apparel Ltd": "Thane, Maharashtra",
                    "Classmate Stationery (ITC Ltd)": "Kolkata, West Bengal",
                    "Dabur India Ltd": "Ghaziabad, Uttar Pradesh",
                }[spec["vendor_name"]],
                {
                    "Samsung India Electronics Pvt Ltd": "29AAACS1234Q1Z5",
                    "Hindustan Unilever Limited": "27AAACH1234Q1Z6",
                    "Nykaa Cosmetics Pvt Ltd": "27AAACN1234Q1Z7",
                    "Raymond Apparel Ltd": "27AAACR1234Q1Z8",
                    "Classmate Stationery (ITC Ltd)": "19AAACT1234Q1Z9",
                    "Dabur India Ltd": "09AAACD1234Q1Z1",
                }[spec["vendor_name"]],
            ),
        )
    for customer in CUSTOMERS:
        customers_by_email[customer["email"]] = ensure_customer(db, tenant.id, customer)

    warehouse = ensure_warehouse(
        db,
        tenant.id,
        {
            "name": WAREHOUSE_LAYOUT["name"],
            "code": WAREHOUSE_LAYOUT["code"],
            "address": WAREHOUSE_LAYOUT["address"],
        },
    )
    locations_by_code: dict[str, WarehouseLocation] = {}
    for sort_order, (code, location_type) in enumerate(WAREHOUSE_LAYOUT["locations"], start=1):
        locations_by_code[code] = ensure_location(db, tenant.id, warehouse.id, code, location_type, sort_order)

    products_by_sku: dict[str, Product] = {}
    for spec in PRODUCT_SPECS:
        products_by_sku[spec["sku"]] = ensure_product(db, tenant.id, categories_by_name[spec["category_name"]].id, spec)
    for product in products_by_sku.values():
        ensure_reorder_rule(db, tenant.id, product.id, warehouse.id, product)

    db.commit()

    inventory_service = InventoryService(db)
    plans = build_receipt_plans()
    for plan in plans:
        product = products_by_sku[plan.sku]
        vendor = vendors_by_name[plan.vendor_name]
        ensure_stock_receipt(
            db,
            tenant.id,
            users[UserRole.INVENTORY_MANAGER].id,
            warehouse.id,
            product,
            vendor.id,
            plan,
            locations_by_code[plan.location_code].id,
        )

    db.commit()

    serials_by_sku: dict[str, list[int]] = {}
    batches_by_sku: dict[str, list[int]] = {}
    inventory_repo = InventoryRepository(db)
    product_sku_by_id = {product.id: sku for sku, product in products_by_sku.items()}
    for serial in inventory_repo.list_serials(tenant.id):
        serials_by_sku.setdefault(product_sku_by_id[serial.product_id], []).append(serial.id)
    for batch in inventory_repo.list_batches(tenant.id):
        batches_by_sku.setdefault(product_sku_by_id[batch.product_id], []).append(batch.id)
    for sku in list(serials_by_sku):
        serials_by_sku[sku].sort()
    for sku in list(batches_by_sku):
        batches_by_sku[sku].sort()

    # Sales order 1: fully fulfilled
    order1 = ensure_sales_order(
        db,
        tenant.id,
        users[UserRole.SALES_STAFF].id,
        customers_by_email["procurement@bigbasket.com"].id,
        "SO-001",
        dt(2025, 4, 15),
        dt(2025, 4, 20),
        "BigBasket replenishment order for flagship categories.",
        [
            {"product_id": products_by_sku["ELEC-TV-SAM43"].id, "ordered_quantity": 5, "unit_price": d("22999.00")},
            {"product_id": products_by_sku["ELEC-HP-BOAT450"].id, "ordered_quantity": 10, "unit_price": d("1299.00")},
            {"product_id": products_by_sku["FOOD-ATTA-ASH10"].id, "ordered_quantity": 20, "unit_price": d("385.00")},
        ],
    )
    reservation_locations_by_sku = {
        spec["sku"]: locations_by_code[spec["receipt_locations"][0]]
        for spec in PRODUCT_SPECS
    }
    reserve_sales_order_inventory(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order1, {p.id: p for p in products_by_sku.values()}, reservation_locations_by_sku)
    create_pick_task_for_order(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order1)
    NotificationService(db).notify_role(
        tenant.id,
        "INVENTORY_MANAGER",
        title="New order to pick: SO-001",
        message="Sales order SO-001 confirmed. Please pick the required stock.",
        type=NotificationType.INFO.value,
        category=NotificationCategory.SALES.value,
        priority=NotificationPriority.NORMAL.value,
        entity_type="sales_order",
        entity_id=str(order1.id),
        action_url=f"/sales/{order1.id}",
    )
    complete_first_sales_order(
        db,
        tenant.id,
        users[UserRole.SALES_STAFF].id,
        order1,
        {product.id: product for product in products_by_sku.values()},
        batches_by_sku,
        serials_by_sku,
    )

    # Return against SO-001
    create_return_for_first_sales_order(
        db,
        tenant.id,
        users[UserRole.SALES_STAFF].id,
        order1,
        products_by_sku,
        locations_by_code,
        serials_by_sku,
    )

    # Sales order 2: confirmed and queued
    order2 = ensure_sales_order(
        db,
        tenant.id,
        users[UserRole.SALES_STAFF].id,
        customers_by_email["vendor@reliancesmart.in"].id,
        "SO-002",
        dt(2025, 5, 8),
        dt(2025, 5, 18),
        "Reliance Smart seasonal replenishment.",
        [
            {"product_id": products_by_sku["FOOD-MILK-AMUL1L"].id, "ordered_quantity": 15, "unit_price": d("75.00")},
            {"product_id": products_by_sku["COS-SUN-LAK100"].id, "ordered_quantity": 10, "unit_price": d("215.00")},
            {"product_id": products_by_sku["CLO-UND-JOC3P"].id, "ordered_quantity": 8, "unit_price": d("349.00")},
        ],
    )
    reserve_sales_order_inventory(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order2, {p.id: p for p in products_by_sku.values()}, reservation_locations_by_sku)
    create_pick_task_for_order(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order2)
    NotificationService(db).notify_role(
        tenant.id,
        "INVENTORY_MANAGER",
        title="New order to pick: SO-002",
        message="Sales order SO-002 confirmed. Please pick the required stock.",
        type=NotificationType.INFO.value,
        category=NotificationCategory.SALES.value,
        priority=NotificationPriority.NORMAL.value,
        entity_type="sales_order",
        entity_id=str(order2.id),
        action_url=f"/sales/{order2.id}",
    )

    # Sales order 3: confirmed and queued
    order3 = ensure_sales_order(
        db,
        tenant.id,
        users[UserRole.SALES_STAFF].id,
        customers_by_email["buying@moreretail.in"].id,
        "SO-003",
        dt(2025, 5, 25),
        dt(2025, 6, 5),
        "More Supermarket fast-moving replenishment order.",
        [
            {"product_id": products_by_sku["HW-CHY-DAB1KG"].id, "ordered_quantity": 12, "unit_price": d("285.00")},
            {"product_id": products_by_sku["STA-PEN-REY50"].id, "ordered_quantity": 30, "unit_price": d("210.00")},
            {"product_id": products_by_sku["CLO-SUIT-RAY3M"].id, "ordered_quantity": 5, "unit_price": d("2699.00")},
        ],
    )
    reserve_sales_order_inventory(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order3, {p.id: p for p in products_by_sku.values()}, reservation_locations_by_sku)
    create_pick_task_for_order(db, tenant.id, users[UserRole.INVENTORY_MANAGER].id, order3)

    # Open reorder purchase order + task + notification
    seed_open_reorder_po(
        db,
        tenant.id,
        users[UserRole.PURCHASE_STAFF].id,
        users[UserRole.PURCHASE_STAFF].id,
        vendors_by_name["Samsung India Electronics Pvt Ltd"].id,
        products_by_sku,
    )

    db.commit()

    summary = {
        "users": db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant.id)) or 0,
        "categories": db.scalar(select(func.count(Category.id)).where(Category.tenant_id == tenant.id)) or 0,
        "vendors": db.scalar(select(func.count(Vendor.id)).where(Vendor.tenant_id == tenant.id)) or 0,
        "customers": db.scalar(select(func.count(Customer.id)).where(Customer.tenant_id == tenant.id)) or 0,
        "products": db.scalar(select(func.count(Product.id)).where(Product.tenant_id == tenant.id)) or 0,
        "warehouses": db.scalar(select(func.count(Warehouse.id)).where(Warehouse.tenant_id == tenant.id)) or 0,
        "warehouse_locations": db.scalar(select(func.count(WarehouseLocation.id)).where(WarehouseLocation.tenant_id == tenant.id)) or 0,
        "reorder_rules": db.scalar(select(func.count(ReorderRule.id)).where(ReorderRule.tenant_id == tenant.id)) or 0,
        "purchase_orders": db.scalar(select(func.count(PurchaseOrder.id)).where(PurchaseOrder.tenant_id == tenant.id)) or 0,
        "purchase_receipts": db.scalar(select(func.count(PurchaseReceipt.id)).where(PurchaseReceipt.tenant_id == tenant.id)) or 0,
        "sales_orders": db.scalar(select(func.count(SalesOrder.id)).where(SalesOrder.tenant_id == tenant.id)) or 0,
        "sales_returns": db.scalar(select(func.count(SalesReturn.id)).where(SalesReturn.tenant_id == tenant.id)) or 0,
        "notifications": db.scalar(select(func.count(Notification.id)).where(Notification.tenant_id == tenant.id)) or 0,
        "workflow_tasks": db.scalar(select(func.count(WorkflowTask.id)).where(WorkflowTask.tenant_id == tenant.id)) or 0,
        "inventory_batches": db.scalar(select(func.count(InventoryBatch.id)).where(InventoryBatch.tenant_id == tenant.id)) or 0,
        "inventory_serials": db.scalar(select(func.count(InventorySerial.id)).where(InventorySerial.tenant_id == tenant.id)) or 0,
        "invoices": db.scalar(select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant.id)) or 0,
    }
    print("Seed complete!")
    print(f"  Tenant: {tenant.company_name}")
    print(f"  Super Admin: {super_admin.email}")
    print(f"  Admin: {users[UserRole.TENANT_ADMIN].email}")
    print("")
    print(f"  Table totals for tenant {tenant.id}:")
    print(f"    - users: {summary['users']}")
    print(f"    - categories: {summary['categories']}")
    print(f"    - vendors: {summary['vendors']}")
    print(f"    - customers: {summary['customers']}")
    print(f"    - products: {summary['products']}")
    print(f"    - warehouses: {summary['warehouses']}")
    print(f"    - warehouse_locations: {summary['warehouse_locations']}")
    print(f"    - reorder_rules: {summary['reorder_rules']}")
    print(f"    - purchase_orders: {summary['purchase_orders']}")
    print(f"    - purchase_receipts: {summary['purchase_receipts']}")
    print(f"    - sales_orders: {summary['sales_orders']}")
    print(f"    - sales_returns: {summary['sales_returns']}")
    print(f"    - inventory_batches: {summary['inventory_batches']}")
    print(f"    - inventory_serials: {summary['inventory_serials']}")
    print(f"    - invoices: {summary['invoices']}")
    return summary


def main() -> None:
    if not is_seed_enabled():
        print("SEED_ON_STARTUP=false; skipping D-Mart seed.")
        return

    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_database(db)


if __name__ == "__main__":
    main()
