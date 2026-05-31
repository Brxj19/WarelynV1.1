"""
Seed script for the Minimalist tenant (admin@minimalist.com).
Run from backend/: .venv/bin/python scripts/seed_minimalist.py

This script is append-only and idempotent:
- it keeps existing data untouched
- it adds deterministic "engine-like" workflow data for tenant_id=1
"""

import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import Bill, Invoice
from app.models.fulfillment import PickTask, PickTaskStatus
from app.models.inventory import WarehouseStock
from app.models.master_data import (
    Brand,
    Category,
    Customer,
    LocationType,
    Product,
    RecordStatus,
    Vendor,
    Warehouse,
    WarehouseLocation,
)
from app.models.operations import PutawayTask, PutawayTaskStatus, ReorderRule, StockCountSession
from app.models.purchasing import PurchaseOrder, PurchaseReceipt
from app.models.returns import SalesReturn, SalesReturnItemStatus
from app.models.sales import SalesFulfillment, SalesOrder, SalesOrderStatus
from app.models.workflow import WorkflowEvent, WorkflowTask
from app.repositories.fulfillment import FulfillmentRepository
from app.services.documents import DocumentsService
from app.services.fulfillment import FulfillmentService
from app.services.operations import CycleCountService, PutawayTaskService
from app.services.purchasing import PurchasingService
from app.services.returns import ReturnsService
from app.services.sales import SalesService


SEED_TAG = "ENGINE-SEED-2026Q2"


def as_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def get_tenant_and_admin(db: Session):
    admin = db.query(User).filter(User.email == "admin@minimalist.com").first()
    if not admin:
        print("ERROR: admin@minimalist.com not found. Register the tenant first via the app.")
        sys.exit(1)
    tenant = db.query(Tenant).filter(Tenant.id == admin.tenant_id).first()
    return tenant, admin


def seed_categories(db: Session, tenant_id: int) -> dict[str, int]:
    categories = [
        {"name": "Face Care", "description": "Cleansers, moisturizers, serums, and face masks"},
        {"name": "Hair Care", "description": "Shampoos, conditioners, oils, and hair treatments"},
        {"name": "Body Care", "description": "Body lotions, scrubs, washes, and sunscreens"},
        {"name": "Lip Care", "description": "Lip balms, tints, and treatments"},
        {"name": "Men's Grooming", "description": "Beard oils, face washes, and grooming kits"},
        {"name": "Wellness", "description": "Supplements, immunity boosters, and health drinks"},
        {"name": "Fragrances", "description": "Perfumes, deodorants, and body mists"},
        {"name": "Baby Care", "description": "Baby lotions, oils, and gentle cleansers"},
    ]
    result = {}
    for cat in categories:
        existing = db.query(Category).filter(Category.tenant_id == tenant_id, Category.name == cat["name"]).first()
        if not existing:
            obj = Category(tenant_id=tenant_id, **cat)
            db.add(obj)
            db.flush()
            result[cat["name"]] = obj.id
        else:
            result[cat["name"]] = existing.id
    return result


def seed_brands(db: Session, tenant_id: int) -> dict[str, int]:
    brands = [
        {"name": "Minimalist", "description": "Science-backed skincare brand from India"},
        {"name": "Mamaearth", "description": "Toxin-free personal care brand"},
        {"name": "Plum Goodness", "description": "Vegan beauty and skincare"},
        {"name": "Dot & Key", "description": "Korean-inspired skincare for Indian skin"},
        {"name": "mCaffeine", "description": "Caffeine-infused personal care"},
        {"name": "Wow Skin Science", "description": "Apple cider vinegar and natural ingredients"},
        {"name": "Forest Essentials", "description": "Luxury Ayurvedic beauty"},
        {"name": "Biotique", "description": "Ayurvedic bio-technology skincare"},
        {"name": "Himalaya Herbals", "description": "Herbal healthcare and personal care"},
        {"name": "Khadi Natural", "description": "Handmade herbal products"},
    ]
    result = {}
    for brand in brands:
        existing = db.query(Brand).filter(Brand.tenant_id == tenant_id, Brand.name == brand["name"]).first()
        if not existing:
            obj = Brand(tenant_id=tenant_id, **brand)
            db.add(obj)
            db.flush()
            result[brand["name"]] = obj.id
        else:
            result[brand["name"]] = existing.id
    return result


def seed_vendors(db: Session, tenant_id: int) -> dict[str, int]:
    vendors = [
        {"name": "Rajesh Chemicals Pvt Ltd", "email": "orders@rajeshchem.in", "phone": "+91-22-2567-8901", "address": "Plot 45, MIDC Andheri East, Mumbai 400093", "gst_number": "27AABCR1234F1Z5"},
        {"name": "Sai Packaging Solutions", "email": "supply@saipack.co.in", "phone": "+91-80-4123-5678", "address": "No. 12, Peenya Industrial Area, Bengaluru 560058", "gst_number": "29AADCS5678G1Z3"},
        {"name": "Gupta Fragrance House", "email": "info@guptafragrance.com", "phone": "+91-11-2345-6789", "address": "B-23, Okhla Phase II, New Delhi 110020", "gst_number": "07AABCG9012H1Z1"},
        {"name": "Patel Herbal Extracts", "email": "procurement@patelherbal.in", "phone": "+91-79-2654-3210", "address": "Survey No. 78, Sanand GIDC, Ahmedabad 382110", "gst_number": "24AABCP3456J1Z7"},
        {"name": "Sharma Glass & Containers", "email": "sales@sharmaglass.co.in", "phone": "+91-141-267-8900", "address": "E-56, Sitapura Industrial Area, Jaipur 302022", "gst_number": "08AABCS7890K1Z4"},
        {"name": "Lakshmi Bio Labs", "email": "orders@lakshmibio.in", "phone": "+91-44-2812-3456", "address": "Plot 89, SIDCO Industrial Estate, Chennai 600032", "gst_number": "33AABCL2345M1Z9"},
        {"name": "Nandi Logistics & Cold Chain", "email": "dispatch@nandilogistics.com", "phone": "+91-40-2345-6780", "address": "Sy No. 34, Shamshabad, Hyderabad 501218", "gst_number": "36AABCN6789P1Z2"},
    ]
    result = {}
    for vendor in vendors:
        existing = db.query(Vendor).filter(Vendor.tenant_id == tenant_id, Vendor.name == vendor["name"]).first()
        if not existing:
            obj = Vendor(tenant_id=tenant_id, **vendor)
            db.add(obj)
            db.flush()
            result[vendor["name"]] = obj.id
        else:
            result[vendor["name"]] = existing.id
    return result


def seed_customers(db: Session, tenant_id: int) -> dict[str, int]:
    customers = [
        {"name": "Nykaa Fashion Pvt Ltd", "email": "vendor-ops@nykaa.com", "phone": "+91-22-6789-0123", "address": "Nykaa HQ, BKC, Mumbai 400051", "gst_number": "27AABCN1234Q1Z6"},
        {"name": "Flipkart Internet Pvt Ltd", "email": "seller-support@flipkart.com", "phone": "+91-80-4567-8901", "address": "Embassy Tech Village, Bengaluru 560103", "gst_number": "29AABCF5678R1Z8"},
        {"name": "Amazon Seller Services", "email": "vendor-central@amazon.in", "phone": "+91-80-2345-6789", "address": "World Trade Center, Brigade Gateway, Bengaluru 560055", "gst_number": "29AABCA9012S1Z3"},
        {"name": "Purplle Beauty Solutions", "email": "brands@purplle.com", "phone": "+91-22-4567-1234", "address": "Andheri West, Mumbai 400053", "gst_number": "27AABCP3456T1Z1"},
        {"name": "Reliance Retail Ltd", "email": "procurement@relianceretail.com", "phone": "+91-22-3567-8900", "address": "Maker Chambers IV, Nariman Point, Mumbai 400021", "gst_number": "27AABCR7890U1Z5"},
        {"name": "BigBasket (Supermarket Grocery)", "email": "brands@bigbasket.com", "phone": "+91-80-6789-0123", "address": "Koramangala, Bengaluru 560034", "gst_number": "29AABCB2345V1Z7"},
        {"name": "Tata 1mg Healthcare", "email": "partnerships@1mg.com", "phone": "+91-124-456-7890", "address": "Sector 44, Gurugram 122003", "gst_number": "06AABCT6789W1Z4"},
        {"name": "Wellness Forever Medicare", "email": "purchase@wellnessforever.in", "phone": "+91-22-2890-1234", "address": "Goregaon East, Mumbai 400063", "gst_number": "27AABCW1234X1Z9"},
    ]
    result = {}
    for customer in customers:
        existing = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.email == customer["email"]).first()
        if not existing:
            obj = Customer(tenant_id=tenant_id, **customer)
            db.add(obj)
            db.flush()
            result[customer["name"]] = obj.id
        else:
            result[customer["name"]] = existing.id
    return result


def seed_products(db: Session, tenant_id: int, categories: dict, brands: dict) -> dict[str, int]:
    products = [
        {"name": "Salicylic Acid 2% Face Wash", "sku": "MIN-FC-001", "barcode": "8906136270101", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("145.00"), "selling_price": Decimal("299.00"), "reorder_level": 500, "description": "Anti-acne face wash with 2% salicylic acid"},
        {"name": "Niacinamide 10% Serum", "sku": "MIN-FC-002", "barcode": "8906136270102", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("210.00"), "selling_price": Decimal("449.00"), "reorder_level": 800, "description": "Pore minimizing and oil control serum 30ml"},
        {"name": "Vitamin C 10% Serum", "sku": "MIN-FC-003", "barcode": "8906136270103", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("250.00"), "selling_price": Decimal("545.00"), "reorder_level": 600, "description": "Brightening serum with ethyl ascorbic acid 30ml"},
        {"name": "Retinol 0.3% Face Cream", "sku": "MIN-FC-004", "barcode": "8906136270104", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("275.00"), "selling_price": Decimal("599.00"), "reorder_level": 400, "description": "Anti-aging night cream with retinol and squalane"},
        {"name": "SPF 50 Sunscreen Gel", "sku": "MIN-BC-001", "barcode": "8906136270201", "category_id": categories["Body Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("180.00"), "selling_price": Decimal("399.00"), "reorder_level": 1000, "description": "Lightweight non-greasy sunscreen 50ml"},
        {"name": "AHA 25% + PHA 5% Peeling Solution", "sku": "MIN-FC-005", "barcode": "8906136270105", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("230.00"), "selling_price": Decimal("499.00"), "reorder_level": 350, "description": "Chemical exfoliant for weekly use 30ml"},
        {"name": "Hair Growth Serum", "sku": "MIN-HC-001", "barcode": "8906136270301", "category_id": categories["Hair Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("320.00"), "selling_price": Decimal("699.00"), "reorder_level": 300, "description": "Redensyl and procapil hair growth serum 60ml"},
        {"name": "Onion Hair Oil", "sku": "MAM-HC-001", "barcode": "8906136270302", "category_id": categories["Hair Care"], "brand_id": brands["Mamaearth"], "unit": "pcs", "cost_price": Decimal("175.00"), "selling_price": Decimal("349.00"), "reorder_level": 600, "description": "Onion oil for hair fall control 250ml"},
        {"name": "Caffeine Face Wash", "sku": "MCA-FC-001", "barcode": "8906136270401", "category_id": categories["Face Care"], "brand_id": brands["mCaffeine"], "unit": "pcs", "cost_price": Decimal("160.00"), "selling_price": Decimal("349.00"), "reorder_level": 450, "description": "Coffee face wash for oil control 100ml"},
        {"name": "Green Tea Face Serum", "sku": "PLM-FC-001", "barcode": "8906136270501", "category_id": categories["Face Care"], "brand_id": brands["Plum Goodness"], "unit": "pcs", "cost_price": Decimal("240.00"), "selling_price": Decimal("525.00"), "reorder_level": 350, "description": "Antioxidant face serum with green tea 30ml"},
        {"name": "Kumkumadi Night Cream", "sku": "FES-FC-001", "barcode": "8906136270601", "category_id": categories["Face Care"], "brand_id": brands["Forest Essentials"], "unit": "pcs", "cost_price": Decimal("850.00"), "selling_price": Decimal("1750.00"), "reorder_level": 150, "description": "Luxury ayurvedic night treatment cream 50g"},
        {"name": "Apple Cider Vinegar Shampoo", "sku": "WOW-HC-001", "barcode": "8906136270701", "category_id": categories["Hair Care"], "brand_id": brands["Wow Skin Science"], "unit": "pcs", "cost_price": Decimal("195.00"), "selling_price": Decimal("399.00"), "reorder_level": 500, "description": "Sulfate-free ACV shampoo 300ml"},
        {"name": "Neem Face Wash", "sku": "HIM-FC-001", "barcode": "8906136270801", "category_id": categories["Face Care"], "brand_id": brands["Himalaya Herbals"], "unit": "pcs", "cost_price": Decimal("65.00"), "selling_price": Decimal("140.00"), "reorder_level": 1200, "description": "Purifying neem face wash 200ml"},
        {"name": "Watermelon Hydrating Serum", "sku": "DOT-FC-001", "barcode": "8906136270901", "category_id": categories["Face Care"], "brand_id": brands["Dot & Key"], "unit": "pcs", "cost_price": Decimal("280.00"), "selling_price": Decimal("595.00"), "reorder_level": 300, "description": "Hydrating serum with watermelon and hyaluronic acid 30ml"},
        {"name": "Rose & Geranium Body Lotion", "sku": "KHD-BC-001", "barcode": "8906136271001", "category_id": categories["Body Care"], "brand_id": brands["Khadi Natural"], "unit": "pcs", "cost_price": Decimal("120.00"), "selling_price": Decimal("275.00"), "reorder_level": 400, "description": "Herbal moisturizing body lotion 210ml"},
        {"name": "Hyaluronic Acid 2% Serum", "sku": "MIN-FC-006", "barcode": "8906136270106", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("195.00"), "selling_price": Decimal("399.00"), "reorder_level": 700, "description": "Deep hydration serum with 5 types of HA 30ml"},
        {"name": "Ceramide Moisturizer", "sku": "MIN-FC-007", "barcode": "8906136270107", "category_id": categories["Face Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("220.00"), "selling_price": Decimal("469.00"), "reorder_level": 500, "description": "Barrier repair moisturizer with ceramides 50ml"},
        {"name": "Lip Balm SPF 30", "sku": "MIN-LC-001", "barcode": "8906136271101", "category_id": categories["Lip Care"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("95.00"), "selling_price": Decimal("199.00"), "reorder_level": 800, "description": "Moisturizing lip balm with sun protection"},
        {"name": "Beard Growth Oil", "sku": "MIN-MG-001", "barcode": "8906136271201", "category_id": categories["Men's Grooming"], "brand_id": brands["Minimalist"], "unit": "pcs", "cost_price": Decimal("185.00"), "selling_price": Decimal("399.00"), "reorder_level": 300, "description": "Redensyl beard growth oil 30ml"},
        {"name": "Caffeine Body Scrub", "sku": "MCA-BC-001", "barcode": "8906136271301", "category_id": categories["Body Care"], "brand_id": brands["mCaffeine"], "unit": "pcs", "cost_price": Decimal("200.00"), "selling_price": Decimal("425.00"), "reorder_level": 350, "description": "Exfoliating coffee body scrub 200g"},
    ]
    result = {}
    for product in products:
        existing = db.query(Product).filter(Product.tenant_id == tenant_id, Product.sku == product["sku"]).first()
        if not existing:
            obj = Product(tenant_id=tenant_id, **product)
            db.add(obj)
            db.flush()
            result[product["sku"]] = obj.id
        else:
            result[product["sku"]] = existing.id
    return result


def seed_warehouses(db: Session, tenant_id: int) -> dict:
    warehouses = [
        {
            "name": "Mumbai Central Warehouse",
            "code": "MUM-CW",
            "address": "Plot 23, TTC Industrial Area, Navi Mumbai 400710",
            "locations": [
                {"name": "Receiving Dock A", "code": "MUM-RCV-A", "location_type": LocationType.RECEIVING},
                {"name": "Receiving Dock B", "code": "MUM-RCV-B", "location_type": LocationType.RECEIVING},
                {"name": "Storage Zone A (Face Care)", "code": "MUM-STR-A", "location_type": LocationType.STORAGE},
                {"name": "Storage Zone B (Hair Care)", "code": "MUM-STR-B", "location_type": LocationType.STORAGE},
                {"name": "Storage Zone C (Body Care)", "code": "MUM-STR-C", "location_type": LocationType.STORAGE},
                {"name": "Picking Area", "code": "MUM-PICK", "location_type": LocationType.PICKING},
                {"name": "Packing Station 1", "code": "MUM-PACK-1", "location_type": LocationType.PACKING},
                {"name": "Packing Station 2", "code": "MUM-PACK-2", "location_type": LocationType.PACKING},
                {"name": "Shipping Bay", "code": "MUM-SHIP", "location_type": LocationType.SHIPPING},
                {"name": "Returns Processing", "code": "MUM-RET", "location_type": LocationType.RETURN},
                {"name": "QC Inspection", "code": "MUM-QC", "location_type": LocationType.QC},
                {"name": "Damaged Goods", "code": "MUM-DMG", "location_type": LocationType.DAMAGED},
            ],
        },
        {
            "name": "Bengaluru Distribution Hub",
            "code": "BLR-DH",
            "address": "Sy No. 56, Bommasandra Industrial Area, Bengaluru 560099",
            "locations": [
                {"name": "Receiving Bay", "code": "BLR-RCV", "location_type": LocationType.RECEIVING},
                {"name": "Main Storage", "code": "BLR-STR-M", "location_type": LocationType.STORAGE},
                {"name": "Cold Storage", "code": "BLR-STR-C", "location_type": LocationType.STORAGE},
                {"name": "Pick Zone", "code": "BLR-PICK", "location_type": LocationType.PICKING},
                {"name": "Pack & Ship", "code": "BLR-PACK", "location_type": LocationType.PACKING},
                {"name": "Dispatch", "code": "BLR-SHIP", "location_type": LocationType.SHIPPING},
                {"name": "Returns", "code": "BLR-RET", "location_type": LocationType.RETURN},
            ],
        },
        {
            "name": "Delhi NCR Fulfillment Center",
            "code": "DEL-FC",
            "address": "Plot 12, Sector 63, Noida 201301",
            "locations": [
                {"name": "Inbound Dock", "code": "DEL-RCV", "location_type": LocationType.RECEIVING},
                {"name": "Bulk Storage", "code": "DEL-STR-B", "location_type": LocationType.STORAGE},
                {"name": "Rack Storage", "code": "DEL-STR-R", "location_type": LocationType.STORAGE},
                {"name": "Pick Wall", "code": "DEL-PICK", "location_type": LocationType.PICKING},
                {"name": "Packing", "code": "DEL-PACK", "location_type": LocationType.PACKING},
                {"name": "Outbound", "code": "DEL-SHIP", "location_type": LocationType.SHIPPING},
            ],
        },
    ]

    result = {}
    for wh_data in warehouses:
        locations_data = wh_data.pop("locations")
        existing = db.query(Warehouse).filter(Warehouse.tenant_id == tenant_id, Warehouse.code == wh_data["code"]).first()
        if not existing:
            wh = Warehouse(tenant_id=tenant_id, **wh_data)
            db.add(wh)
            db.flush()
        else:
            wh = existing

        wh_locs = {}
        for loc_data in locations_data:
            existing_loc = db.query(WarehouseLocation).filter(
                WarehouseLocation.tenant_id == tenant_id,
                WarehouseLocation.warehouse_id == wh.id,
                WarehouseLocation.code == loc_data["code"],
            ).first()
            if not existing_loc:
                loc = WarehouseLocation(tenant_id=tenant_id, warehouse_id=wh.id, **loc_data)
                db.add(loc)
                db.flush()
                wh_locs[loc_data["code"]] = loc.id
            else:
                wh_locs[loc_data["code"]] = existing_loc.id

        result[wh_data["code"] if "code" in wh_data else wh.code] = {"id": wh.id, "locations": wh_locs}
        wh_data["locations"] = locations_data

    return result


def seed_reorder_rules(db: Session, tenant_id: int, products: dict, warehouses: dict):
    mum_wh_id = warehouses["MUM-CW"]["id"]
    rules = [
        {"sku": "MIN-FC-001", "min_qty": 500, "max_qty": 3000, "safety": 200},
        {"sku": "MIN-FC-002", "min_qty": 800, "max_qty": 5000, "safety": 300},
        {"sku": "MIN-FC-003", "min_qty": 600, "max_qty": 4000, "safety": 250},
        {"sku": "MIN-BC-001", "min_qty": 1000, "max_qty": 6000, "safety": 400},
        {"sku": "MIN-HC-001", "min_qty": 300, "max_qty": 2000, "safety": 100},
    ]
    for rule_data in rules:
        product_id = products.get(rule_data["sku"])
        if not product_id:
            continue
        existing = db.query(ReorderRule).filter(
            ReorderRule.tenant_id == tenant_id,
            ReorderRule.product_id == product_id,
            ReorderRule.warehouse_id == mum_wh_id,
        ).first()
        if not existing:
            rule = ReorderRule(
                tenant_id=tenant_id,
                product_id=product_id,
                warehouse_id=mum_wh_id,
                min_quantity=Decimal(str(rule_data["min_qty"])),
                max_quantity=Decimal(str(rule_data["max_qty"])),
                safety_stock=Decimal(str(rule_data["safety"])),
                is_active=True,
            )
            db.add(rule)


def seed_stock(db: Session, tenant_id: int, admin_id: int, products: dict, warehouses: dict):
    from app.services.inventory import InventoryService

    svc = InventoryService(db)
    mum = warehouses["MUM-CW"]
    blr = warehouses["BLR-DH"]
    delhi = warehouses["DEL-FC"]

    stock_plan = [
        {"sku": "MIN-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 2500},
        {"sku": "MIN-FC-002", "wh": mum, "loc_code": "MUM-STR-A", "qty": 3200},
        {"sku": "MIN-FC-003", "wh": mum, "loc_code": "MUM-STR-A", "qty": 1800},
        {"sku": "MIN-FC-004", "wh": mum, "loc_code": "MUM-STR-A", "qty": 1200},
        {"sku": "MIN-FC-005", "wh": mum, "loc_code": "MUM-STR-A", "qty": 900},
        {"sku": "MIN-FC-006", "wh": mum, "loc_code": "MUM-STR-A", "qty": 2100},
        {"sku": "MIN-FC-007", "wh": mum, "loc_code": "MUM-STR-A", "qty": 1500},
        {"sku": "MIN-BC-001", "wh": mum, "loc_code": "MUM-STR-C", "qty": 4000},
        {"sku": "MIN-HC-001", "wh": mum, "loc_code": "MUM-STR-B", "qty": 800},
        {"sku": "MIN-LC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 2000},
        {"sku": "MIN-MG-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 600},
        {"sku": "MAM-HC-001", "wh": mum, "loc_code": "MUM-STR-B", "qty": 1500},
        {"sku": "MCA-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 1100},
        {"sku": "MCA-BC-001", "wh": mum, "loc_code": "MUM-STR-C", "qty": 800},
        {"sku": "PLM-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 900},
        {"sku": "FES-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 350},
        {"sku": "WOW-HC-001", "wh": mum, "loc_code": "MUM-STR-B", "qty": 1300},
        {"sku": "HIM-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 3500},
        {"sku": "DOT-FC-001", "wh": mum, "loc_code": "MUM-STR-A", "qty": 750},
        {"sku": "KHD-BC-001", "wh": mum, "loc_code": "MUM-STR-C", "qty": 1000},
        {"sku": "MIN-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 800},
        {"sku": "MIN-FC-002", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1200},
        {"sku": "MIN-BC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1500},
        {"sku": "MAM-HC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 600},
        {"sku": "MCA-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 500},
        {"sku": "HIM-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1000},
        {"sku": "MIN-FC-001", "wh": delhi, "loc_code": "DEL-STR-R", "qty": 600},
        {"sku": "MIN-FC-002", "wh": delhi, "loc_code": "DEL-STR-R", "qty": 900},
        {"sku": "MIN-FC-003", "wh": delhi, "loc_code": "DEL-STR-R", "qty": 500},
        {"sku": "MIN-BC-001", "wh": delhi, "loc_code": "DEL-STR-B", "qty": 1000},
        {"sku": "WOW-HC-001", "wh": delhi, "loc_code": "DEL-STR-R", "qty": 700},
    ]

    stocked = 0
    for entry in stock_plan:
        product_id = products.get(entry["sku"])
        if not product_id:
            continue
        wh = entry["wh"]
        loc_id = wh["locations"].get(entry["loc_code"])
        if not loc_id:
            continue
        idempotency_key = f"seed-{entry['sku']}-{entry['loc_code']}"
        try:
            svc.stock_in(
                tenant_id,
                admin_id,
                {
                    "product_id": product_id,
                    "warehouse_id": wh["id"],
                    "location_id": loc_id,
                    "quantity": str(entry["qty"]),
                    "idempotency_key": idempotency_key,
                },
            )
            stocked += 1
        except Exception:
            pass
    return stocked


def seed_buffer_stock(db: Session, tenant_id: int, admin_id: int, products: dict[str, int], warehouses: dict) -> int:
    """
    Add a deterministic safety buffer so repeat runs can still progress workflow states
    without failing reservation checks. Idempotency keys prevent duplicate inserts.
    """
    from app.services.inventory import InventoryService

    svc = InventoryService(db)
    wh_id = warehouses["MUM-CW"]["id"]
    loc_id = warehouses["MUM-CW"]["locations"]["MUM-STR-A"]
    buffer_skus = sorted(products.keys())
    inserted = 0
    for sku in buffer_skus:
        product_id = products.get(sku)
        if not product_id:
            continue
        try:
            svc.stock_in(
                tenant_id,
                admin_id,
                {
                    "product_id": product_id,
                    "warehouse_id": wh_id,
                    "location_id": loc_id,
                    "quantity": "1500",
                    "idempotency_key": f"{SEED_TAG}-buffer-{sku}",
                },
            )
            inserted += 1
        except Exception:
            pass
    return inserted


def ensure_role_users(db: Session, tenant_id: int) -> dict[str, User]:
    users_to_seed = [
        {"name": "Minimalist Inventory Lead", "email": "inventory.manager@minimalist.com", "role": UserRole.INVENTORY_MANAGER},
        {"name": "Minimalist Sales Ops", "email": "sales.staff@minimalist.com", "role": UserRole.SALES_STAFF},
        {"name": "Minimalist Purchase Ops", "email": "purchase.staff@minimalist.com", "role": UserRole.PURCHASE_STAFF},
        {"name": "Minimalist Business Viewer", "email": "viewer@minimalist.com", "role": UserRole.VIEWER},
    ]
    out: dict[str, User] = {}
    for user_data in users_to_seed:
        user = db.query(User).filter(User.email == user_data["email"]).first()
        if user is None:
            user = User(
                tenant_id=tenant_id,
                name=user_data["name"],
                email=user_data["email"],
                password_hash=get_password_hash("Warelyn@123"),
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            db.flush()
        out[user_data["role"].value] = user
    db.commit()
    return out


def load_products(db: Session, tenant_id: int) -> dict[str, Product]:
    rows = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    return {row.sku: row for row in rows}


def purchase_order_by_number(db: Session, tenant_id: int, po_number: str) -> PurchaseOrder | None:
    return db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.po_number == po_number).first()


def sales_order_by_number(db: Session, tenant_id: int, order_number: str) -> SalesOrder | None:
    return db.query(SalesOrder).filter(SalesOrder.tenant_id == tenant_id, SalesOrder.order_number == order_number).first()


def return_by_number(db: Session, tenant_id: int, return_number: str) -> SalesReturn | None:
    return db.query(SalesReturn).filter(SalesReturn.tenant_id == tenant_id, SalesReturn.return_number == return_number).first()


def receipt_by_number(db: Session, tenant_id: int, receipt_number: str) -> PurchaseReceipt | None:
    return db.query(PurchaseReceipt).filter(PurchaseReceipt.tenant_id == tenant_id, PurchaseReceipt.receipt_number == receipt_number).first()


def allocations_for_order(db: Session, tenant_id: int, order: SalesOrder, split_first_item: bool = False) -> list[dict[str, Any]]:
    allocations: list[dict[str, Any]] = []
    for item_index, item in enumerate(order.items):
        required = as_decimal(item.ordered_quantity)
        if required <= Decimal("0"):
            continue
        stocks = (
            db.query(WarehouseStock)
            .filter(
                WarehouseStock.tenant_id == tenant_id,
                WarehouseStock.product_id == item.product_id,
                WarehouseStock.quantity_available > 0,
            )
            .order_by(WarehouseStock.quantity_available.desc(), WarehouseStock.id.asc())
            .all()
        )
        if not stocks:
            raise RuntimeError(f"No available stock for product_id={item.product_id} while allocating order {order.order_number}")

        remaining = required
        if split_first_item and item_index == 0 and required > Decimal("2"):
            first_qty = min(remaining - Decimal("1"), stocks[0].quantity_available)
            first_qty = first_qty.quantize(Decimal("0.001"))
            if first_qty > Decimal("0"):
                allocations.append(
                    {
                        "sales_order_item_id": item.id,
                        "warehouse_id": stocks[0].warehouse_id,
                        "location_id": stocks[0].location_id,
                        "quantity": first_qty,
                    }
                )
                remaining -= first_qty

        for stock in stocks:
            if remaining <= Decimal("0"):
                break
            alloc_qty = min(remaining, as_decimal(stock.quantity_available)).quantize(Decimal("0.001"))
            if alloc_qty <= Decimal("0"):
                continue
            allocations.append(
                {
                    "sales_order_item_id": item.id,
                    "warehouse_id": stock.warehouse_id,
                    "location_id": stock.location_id,
                    "quantity": alloc_qty,
                }
            )
            remaining -= alloc_qty

        if remaining > Decimal("0"):
            raise RuntimeError(f"Insufficient stock to allocate order {order.order_number}, missing {remaining} for item {item.id}")
    return allocations


def complete_putaway_for_receipt(
    db: Session,
    tenant_id: int,
    receipt_id: int,
    actor_id: int,
    max_items: int | None = None,
) -> int:
    putaway_service = PutawayTaskService(db)
    tasks = (
        db.query(PutawayTask)
        .filter(PutawayTask.tenant_id == tenant_id, PutawayTask.receipt_id == receipt_id)
        .order_by(PutawayTask.id.asc())
        .all()
    )
    done = 0
    for task in tasks:
        if max_items is not None and done >= max_items:
            break
        if task.status == PutawayTaskStatus.COMPLETED:
            done += 1
            continue
        if task.status == PutawayTaskStatus.CANCELLED:
            continue
        if task.status == PutawayTaskStatus.PENDING:
            putaway_service.start(tenant_id, task.id)
        putaway_service.complete(tenant_id, actor_id, task.id, to_location_id=task.to_location_id)
        done += 1
    return done


def seed_purchase_workflows(
    db: Session,
    tenant_id: int,
    users_by_role: dict[str, User],
    products_by_sku: dict[str, Product],
    vendors: dict[str, int],
    warehouses: dict[str, dict[str, Any]],
) -> dict[str, PurchaseOrder]:
    purchase_user = users_by_role["PURCHASE_STAFF"]
    inventory_user = users_by_role["INVENTORY_MANAGER"]
    admin_user = users_by_role["TENANT_ADMIN"]

    purchasing = PurchasingService(db)
    docs = DocumentsService(db)

    po_plans = [
        {
            "number": "MIN-PO-2026-001",
            "vendor": "Rajesh Chemicals Pvt Ltd",
            "days_ago": 40,
            "expected_in_days": -10,
            "items": [("MIN-FC-001", 300, "145.00"), ("MIN-FC-002", 240, "210.00")],
            "submit": False,
        },
        {
            "number": "MIN-PO-2026-002",
            "vendor": "Sai Packaging Solutions",
            "days_ago": 35,
            "expected_in_days": -5,
            "items": [("MIN-BC-001", 500, "178.00"), ("MIN-HC-001", 120, "315.00")],
            "submit": True,
        },
        {
            "number": "MIN-PO-2026-003",
            "vendor": "Patel Herbal Extracts",
            "days_ago": 30,
            "expected_in_days": 4,
            "items": [("HIM-FC-001", 900, "62.00"), ("WOW-HC-001", 240, "190.00")],
            "submit": True,
            "approve": True,
        },
        {
            "number": "MIN-PO-2026-004",
            "vendor": "Lakshmi Bio Labs",
            "days_ago": 26,
            "expected_in_days": -1,
            "items": [("MIN-FC-003", 420, "248.00"), ("MIN-FC-006", 360, "190.00")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "MIN-RCPT-2026-004-A",
                    "wh_code": "MUM-CW",
                    "loc_code": "MUM-RCV-A",
                    "lines": [("MIN-FC-003", 200), ("MIN-FC-006", 120)],
                    "complete_putaway": 1,
                }
            ],
        },
        {
            "number": "MIN-PO-2026-005",
            "vendor": "Gupta Fragrance House",
            "days_ago": 24,
            "expected_in_days": -2,
            "items": [("MIN-FC-004", 180, "272.00"), ("MIN-FC-005", 180, "228.00"), ("MCA-FC-001", 240, "158.00")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "MIN-RCPT-2026-005-A",
                    "wh_code": "BLR-DH",
                    "loc_code": "BLR-RCV",
                    "lines": [("MIN-FC-004", 180), ("MIN-FC-005", 180), ("MCA-FC-001", 240)],
                }
            ],
        },
        {
            "number": "MIN-PO-2026-006",
            "vendor": "Sharma Glass & Containers",
            "days_ago": 21,
            "expected_in_days": -1,
            "items": [("MIN-LC-001", 600, "93.00"), ("KHD-BC-001", 300, "118.00")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "MIN-RCPT-2026-006-A",
                    "wh_code": "DEL-FC",
                    "loc_code": "DEL-RCV",
                    "lines": [("MIN-LC-001", 600), ("KHD-BC-001", 300)],
                    "complete_putaway": "all",
                }
            ],
            "bill_action": "PAID",
        },
        {
            "number": "MIN-PO-2026-007",
            "vendor": "Nandi Logistics & Cold Chain",
            "days_ago": 19,
            "expected_in_days": 3,
            "items": [("MAM-HC-001", 250, "170.00"), ("PLM-FC-001", 180, "236.00")],
            "cancel": True,
        },
        {
            "number": "MIN-PO-2026-008",
            "vendor": "Rajesh Chemicals Pvt Ltd",
            "days_ago": 16,
            "expected_in_days": -2,
            "items": [("MIN-MG-001", 220, "180.00"), ("MCA-BC-001", 180, "197.00"), ("DOT-FC-001", 140, "276.00")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "MIN-RCPT-2026-008-A",
                    "wh_code": "MUM-CW",
                    "loc_code": "MUM-RCV-B",
                    "lines": [("MIN-MG-001", 220), ("MCA-BC-001", 180), ("DOT-FC-001", 140)],
                    "complete_putaway": "all",
                }
            ],
            "bill_action": "DRAFT",
        },
        {
            "number": "MIN-PO-2026-009",
            "vendor": "Sai Packaging Solutions",
            "days_ago": 14,
            "expected_in_days": 5,
            "items": [("MIN-FC-007", 300, "218.00"), ("FES-FC-001", 80, "845.00")],
            "submit": True,
            "approve": True,
        },
        {
            "number": "MIN-PO-2026-010",
            "vendor": "Patel Herbal Extracts",
            "days_ago": 12,
            "expected_in_days": -1,
            "items": [("MIN-FC-001", 260, "146.00"), ("MIN-FC-002", 210, "211.00"), ("MIN-BC-001", 320, "179.00")],
            "submit": True,
            "approve": True,
            "receipts": [
                {
                    "number": "MIN-RCPT-2026-010-A",
                    "wh_code": "MUM-CW",
                    "loc_code": "MUM-RCV-A",
                    "lines": [("MIN-FC-001", 260), ("MIN-FC-002", 210), ("MIN-BC-001", 320)],
                    "complete_putaway": "all",
                }
            ],
            "bill_action": "SENT",
        },
    ]

    out: dict[str, PurchaseOrder] = {}
    today = date.today()

    for idx, plan in enumerate(po_plans, start=1):
        existing_po = purchase_order_by_number(db, tenant_id, plan["number"])
        if existing_po is None:
            payload_items = []
            for sku, qty, unit_cost in plan["items"]:
                product = products_by_sku[sku]
                payload_items.append(
                    {
                        "product_id": product.id,
                        "ordered_quantity": as_decimal(qty),
                        "unit_cost": as_decimal(unit_cost),
                        "notes": f"{SEED_TAG} {plan['number']} line",
                    }
                )
            po = purchasing.create_purchase_order(
                tenant_id,
                purchase_user.id,
                {
                    "vendor_id": vendors[plan["vendor"]],
                    "po_number": plan["number"],
                    "order_date": today - timedelta(days=plan["days_ago"]),
                    "expected_date": max(
                        today - timedelta(days=plan["days_ago"]),
                        today,
                        today + timedelta(days=plan["expected_in_days"]),
                    ),
                    "notes": f"{SEED_TAG} purchase workflow seed {idx}",
                    "items": payload_items,
                },
            )
        else:
            po = purchasing.get_purchase_order(tenant_id, existing_po.id)
            min_expected_date = max(po.order_date, po.created_at.date())
            if po.expected_date is not None and po.expected_date < min_expected_date:
                po.expected_date = min_expected_date
                db.commit()

        if plan.get("submit") and po.status == po.status.DRAFT:
            po = purchasing.submit_purchase_order(tenant_id, purchase_user.id, po.id)
        if plan.get("approve") and po.status == po.status.SUBMITTED:
            po = purchasing.approve_purchase_order(tenant_id, po.id, admin_user.id)
        if plan.get("cancel") and po.status in (po.status.DRAFT, po.status.SUBMITTED):
            po = purchasing.cancel_purchase_order(tenant_id, po.id)

        receipts = plan.get("receipts", [])
        for rcpt_plan in receipts:
            existing_receipt = receipt_by_number(db, tenant_id, rcpt_plan["number"])
            if existing_receipt is None:
                refreshed_po = purchasing.get_purchase_order(tenant_id, po.id)
                po_item_by_product = {item.product_id: item for item in refreshed_po.items}
                wh = warehouses[rcpt_plan["wh_code"]]
                loc_id = wh["locations"][rcpt_plan["loc_code"]]
                receipt_items = []
                for sku, qty in rcpt_plan["lines"]:
                    product_id = products_by_sku[sku].id
                    receipt_items.append(
                        {
                            "purchase_order_item_id": po_item_by_product[product_id].id,
                            "product_id": product_id,
                            "warehouse_id": wh["id"],
                            "location_id": loc_id,
                            "received_quantity": as_decimal(qty),
                        }
                    )
                receipt = purchasing.create_receipt(
                    tenant_id,
                    inventory_user.id,
                    po.id,
                    {
                        "receipt_number": rcpt_plan["number"],
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
                    {
                        "idempotency_key": f"{SEED_TAG}:{plan['number']}:{rcpt_plan['number']}",
                        "note": f"{SEED_TAG} committed receipt",
                    },
                )
                receipt = purchasing.get_receipt(tenant_id, receipt.id)

            complete_putaway = rcpt_plan.get("complete_putaway")
            if complete_putaway:
                max_items = None if complete_putaway == "all" else int(complete_putaway)
                complete_putaway_for_receipt(db, tenant_id, receipt.id, inventory_user.id, max_items=max_items)

        bill_action = plan.get("bill_action")
        if bill_action:
            bill = db.query(Bill).filter(Bill.tenant_id == tenant_id, Bill.purchase_order_id == po.id).first()
            if bill is None:
                try:
                    created = docs.create_bill(
                        tenant_id,
                        purchase_user.id,
                        {
                            "purchase_order_id": po.id,
                            "issue_date": today - timedelta(days=max(1, plan["days_ago"] // 2)),
                            "due_date": today + timedelta(days=15),
                            "notes": f"{SEED_TAG} bill for {plan['number']}",
                        },
                    )
                    bill = docs.get_bill(tenant_id, created.id)
                except Exception:
                    bill = None
            if bill is not None:
                if bill_action in {"SENT", "PAID"} and bill.status == bill.status.DRAFT:
                    try:
                        bill = docs.send_bill(tenant_id, bill.id, purchase_user.id)
                    except Exception:
                        bill = docs.get_bill(tenant_id, bill.id)
                if bill_action == "PAID" and bill.status != bill.status.PAID:
                    try:
                        docs.mark_bill_paid(tenant_id, bill.id, purchase_user.id)
                    except Exception:
                        pass

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

    so_plans = [
        {
            "number": "MIN-SO-2026-001",
            "customer": "Nykaa Fashion Pvt Ltd",
            "days_ago": 21,
            "ship_in_days": 2,
            "items": [("MIN-FC-001", 60), ("MIN-FC-002", 40)],
            "state": "DRAFT",
        },
        {
            "number": "MIN-SO-2026-002",
            "customer": "Flipkart Internet Pvt Ltd",
            "days_ago": 18,
            "ship_in_days": 1,
            "items": [("MIN-BC-001", 80), ("MIN-FC-003", 50)],
            "state": "CONFIRMED",
        },
        {
            "number": "MIN-SO-2026-003",
            "customer": "Amazon Seller Services",
            "days_ago": 17,
            "ship_in_days": 1,
            "items": [("MAM-HC-001", 75), ("MIN-FC-006", 55)],
            "state": "CANCELLED",
        },
        {
            "number": "MIN-SO-2026-004",
            "customer": "Purplle Beauty Solutions",
            "days_ago": 15,
            "ship_in_days": 0,
            "items": [("MIN-FC-004", 35), ("MIN-FC-005", 40), ("MCA-FC-001", 50)],
            "state": "FULFILLED_DRAFT_INVOICE",
        },
        {
            "number": "MIN-SO-2026-005",
            "customer": "Reliance Retail Ltd",
            "days_ago": 14,
            "ship_in_days": -1,
            "items": [("HIM-FC-001", 180), ("MIN-BC-001", 140)],
            "state": "FULFILLED_SENT_INVOICE",
        },
        {
            "number": "MIN-SO-2026-006",
            "customer": "BigBasket (Supermarket Grocery)",
            "days_ago": 13,
            "ship_in_days": -1,
            "items": [("MIN-FC-007", 70), ("MIN-LC-001", 150), ("KHD-BC-001", 90)],
            "state": "FULFILLED_PAID_INVOICE",
        },
        {
            "number": "MIN-SO-2026-007",
            "customer": "Tata 1mg Healthcare",
            "days_ago": 12,
            "ship_in_days": 1,
            "items": [("MIN-FC-001", 45), ("MIN-FC-002", 30)],
            "state": "PARTIALLY_FULFILLED",
        },
        {
            "number": "MIN-SO-2026-008",
            "customer": "Wellness Forever Medicare",
            "days_ago": 11,
            "ship_in_days": 0,
            "items": [("WOW-HC-001", 60), ("DOT-FC-001", 35)],
            "state": "FULFILLED_FOR_RETURN",
        },
        {
            "number": "MIN-SO-2026-009",
            "customer": "Nykaa Fashion Pvt Ltd",
            "days_ago": 9,
            "ship_in_days": 2,
            "items": [("MIN-MG-001", 40), ("MCA-BC-001", 25)],
            "state": "FULFILLED_FOR_RETURN",
        },
        {
            "number": "MIN-SO-2026-010",
            "customer": "Flipkart Internet Pvt Ltd",
            "days_ago": 7,
            "ship_in_days": 1,
            "items": [("MIN-FC-003", 70), ("PLM-FC-001", 40)],
            "state": "CONFIRMED",
        },
        {
            "number": "MIN-SO-2026-011",
            "customer": "Amazon Seller Services",
            "days_ago": 6,
            "ship_in_days": 2,
            "items": [("MIN-FC-006", 55), ("MIN-FC-007", 45), ("MIN-LC-001", 100)],
            "state": "FULFILLED_DRAFT_INVOICE",
        },
        {
            "number": "MIN-SO-2026-012",
            "customer": "Purplle Beauty Solutions",
            "days_ago": 5,
            "ship_in_days": 3,
            "items": [("MIN-FC-001", 35), ("MCA-FC-001", 35), ("HIM-FC-001", 120)],
            "state": "DRAFT",
        },
    ]

    out: dict[str, SalesOrder] = {}
    today = date.today()

    for idx, plan in enumerate(so_plans, start=1):
        existing_so = sales_order_by_number(db, tenant_id, plan["number"])
        if existing_so is None:
            payload_items = []
            for sku, qty in plan["items"]:
                product = products_by_sku[sku]
                payload_items.append(
                    {
                        "product_id": product.id,
                        "ordered_quantity": as_decimal(qty),
                        "unit_price": as_decimal(product.selling_price),
                        "notes": f"{SEED_TAG} sales line",
                    }
                )
            so = sales.create_sales_order(
                tenant_id,
                sales_user.id,
                {
                    "customer_id": customers[plan["customer"]],
                    "order_number": plan["number"],
                    "order_date": today - timedelta(days=plan["days_ago"]),
                    "expected_ship_date": max(
                        today - timedelta(days=plan["days_ago"]),
                        today,
                        today + timedelta(days=plan["ship_in_days"]),
                    ),
                    "notes": f"{SEED_TAG} sales workflow seed {idx}",
                    "items": payload_items,
                },
            )
        else:
            so = sales.get_sales_order(tenant_id, existing_so.id)
            min_expected_ship_date = max(so.order_date, so.created_at.date())
            if so.expected_ship_date is not None and so.expected_ship_date < min_expected_ship_date:
                so.expected_ship_date = min_expected_ship_date
                db.commit()

        state = plan["state"]
        needs_confirm = state not in {"DRAFT", "CANCELLED"}
        if needs_confirm and so.status == so.status.DRAFT:
            allocations = allocations_for_order(db, tenant_id, so, split_first_item=(state == "PARTIALLY_FULFILLED"))
            sales.confirm_sales_order(
                tenant_id,
                sales_user.id,
                so.id,
                {
                    "idempotency_key": f"{SEED_TAG}:{plan['number']}:confirm",
                    "note": f"{SEED_TAG} confirm {plan['number']}",
                    "allocations": allocations,
                },
            )
            so = sales.get_sales_order(tenant_id, so.id)

        if state == "CANCELLED" and so.status in (SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED):
            sales.cancel_sales_order(
                tenant_id,
                sales_user.id,
                so.id,
                {"idempotency_key": f"{SEED_TAG}:{plan['number']}:cancel", "note": f"{SEED_TAG} cancelled"},
            )
            so = sales.get_sales_order(tenant_id, so.id)

        if state.startswith("FULFILLED") or state == "PARTIALLY_FULFILLED":
            if state == "PARTIALLY_FULFILLED":
                reservations = fulfillment_repo.active_reservations_for_order(tenant_id, so.order_number)
                if reservations:
                    existing_ful = db.query(SalesFulfillment).filter(SalesFulfillment.tenant_id == tenant_id, SalesFulfillment.fulfillment_number == f"{SEED_TAG}-FUL-{plan['number']}-P1").first()
                    if existing_ful is None:
                        reservation = reservations[0]
                        order_item = next((item for item in so.items if item.product_id == reservation.product_id), None)
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
                                            "product_id": reservation.product_id,
                                            "warehouse_id": reservation.warehouse_id,
                                            "location_id": reservation.location_id,
                                            "reservation_id": reservation.id,
                                            "fulfilled_quantity": reservation.quantity,
                                        }
                                    ],
                                },
                            )
                            sales.commit_fulfillment(
                                tenant_id,
                                inventory_user.id,
                                fulfillment.id,
                                {
                                    "idempotency_key": f"{SEED_TAG}:{plan['number']}:partial-commit",
                                    "note": f"{SEED_TAG} partial commit",
                                },
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

        if state.startswith("FULFILLED"):
            invoice = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.sales_order_id == so.id).first()
            if invoice is None:
                try:
                    created = docs.create_invoice(
                        tenant_id,
                        sales_user.id,
                        {
                            "sales_order_id": so.id,
                            "issue_date": today - timedelta(days=1),
                            "due_date": today + timedelta(days=14),
                            "notes": f"{SEED_TAG} invoice for {plan['number']}",
                        },
                    )
                    invoice = docs.get_invoice(tenant_id, created.id)
                except Exception:
                    invoice = None
            if invoice is not None:
                if state == "FULFILLED_SENT_INVOICE" and invoice.status == invoice.status.DRAFT:
                    try:
                        docs.send_invoice(tenant_id, invoice.id, sales_user.id)
                    except Exception:
                        pass
                if state == "FULFILLED_PAID_INVOICE":
                    if invoice.status == invoice.status.DRAFT:
                        try:
                            docs.send_invoice(tenant_id, invoice.id, sales_user.id)
                        except Exception:
                            pass
                    fresh_invoice = docs.get_invoice(tenant_id, invoice.id)
                    if fresh_invoice.status != fresh_invoice.status.PAID:
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

    return_plans = [
        {"number": "MIN-RET-2026-001", "order": "MIN-SO-2026-008", "state": "DRAFT", "qc": None},
        {"number": "MIN-RET-2026-002", "order": "MIN-SO-2026-009", "state": "SUBMITTED", "qc": None},
        {"number": "MIN-RET-2026-003", "order": "MIN-SO-2026-006", "state": "INSPECTION_PENDING", "qc": "RESTOCK"},
        {"number": "MIN-RET-2026-004", "order": "MIN-SO-2026-011", "state": "PROCESSED", "qc": "MIXED"},
        {"number": "MIN-RET-2026-005", "order": "MIN-SO-2026-004", "state": "CANCELLED", "qc": None},
    ]

    ret_loc_warehouse = warehouses["MUM-CW"]["id"]
    ret_location = warehouses["MUM-CW"]["locations"]["MUM-RET"]
    out: dict[str, SalesReturn] = {}

    for plan in return_plans:
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
                    "reason": f"{SEED_TAG} customer return",
                    "notes": f"{SEED_TAG} return workflow",
                    "items": [
                        {
                            "sales_order_item_id": source_item.id,
                            "warehouse_id": ret_loc_warehouse,
                            "location_id": ret_location,
                            "returned_quantity": qty,
                            "reason": "Damaged during transit",
                            "notes": f"{SEED_TAG} intake",
                        }
                    ],
                },
            )
            sales_return = returns_service.get_return(tenant_id, created.id)
        else:
            sales_return = returns_service.get_return(tenant_id, existing.id)

        if plan["state"] in {"SUBMITTED", "INSPECTION_PENDING", "PROCESSED"} and sales_return.status == sales_return.status.DRAFT:
            sales_return = returns_service.submit_return(tenant_id, sales_user.id, sales_return.id)
        if plan["state"] == "CANCELLED" and sales_return.status in (
            sales_return.status.DRAFT,
            sales_return.status.SUBMITTED,
            sales_return.status.INSPECTION_PENDING,
        ):
            sales_return = returns_service.cancel_return(tenant_id, sales_return.id)

        if plan["state"] in {"INSPECTION_PENDING", "PROCESSED"} and sales_return.status in (
            sales_return.status.SUBMITTED,
            sales_return.status.INSPECTION_PENDING,
        ):
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
                {"idempotency_key": f"{SEED_TAG}:{plan['number']}:process", "note": f"{SEED_TAG} process return"},
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
            "key": "MIN-CC-2026-DRAFT",
            "warehouse_code": "MUM-CW",
            "state": "DRAFT",
            "lines": [("MIN-FC-001", "MUM-STR-A", Decimal("2480")), ("MIN-BC-001", "MUM-STR-C", Decimal("3985"))],
        },
        {
            "key": "MIN-CC-2026-SUBMITTED",
            "warehouse_code": "BLR-DH",
            "state": "SUBMITTED",
            "lines": [("MIN-FC-002", "BLR-STR-M", Decimal("1190")), ("HIM-FC-001", "BLR-STR-M", Decimal("995"))],
        },
        {
            "key": "MIN-CC-2026-RECONCILED",
            "warehouse_code": "DEL-FC",
            "state": "RECONCILED",
            "lines": [("MIN-FC-003", "DEL-STR-R", Decimal("488")), ("MIN-BC-001", "DEL-STR-B", Decimal("1012"))],
        },
        {
            "key": "MIN-CC-2026-CANCELLED",
            "warehouse_code": "MUM-CW",
            "state": "CANCELLED",
            "lines": [("MIN-FC-006", "MUM-STR-A", Decimal("2090"))],
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
            session = cycle_service.create_session(
                tenant_id,
                inventory_user.id,
                {"warehouse_id": warehouse_id, "notes": f"{SEED_TAG} {plan['key']}"},
            )
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
                cycle_service.update_line(
                    tenant_id,
                    session.id,
                    line.id,
                    {"counted_quantity": counted_qty, "notes": f"{SEED_TAG} counted"},
                )

        session = cycle_service.get_session(tenant_id, session.id)
        if plan["state"] in {"SUBMITTED", "RECONCILED"} and session.status in (session.status.DRAFT, session.status.IN_PROGRESS):
            session = cycle_service.submit(tenant_id, session.id)
        if plan["state"] == "RECONCILED" and session.status == session.status.SUBMITTED:
            session, _ = cycle_service.reconcile(tenant_id, session.id, inventory_user.id)
        if plan["state"] == "CANCELLED" and session.status not in (session.status.CANCELLED, session.status.RECONCILED):
            session = cycle_service.cancel_session(tenant_id, session.id)
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
    }


def main():
    db = SessionLocal()
    try:
        tenant, admin = get_tenant_and_admin(db)
        print(f"Seeding data for tenant: {tenant.company_name} (ID: {tenant.id})")

        categories = seed_categories(db, tenant.id)
        print(f"  Categories: {len(categories)} seeded")

        brands = seed_brands(db, tenant.id)
        print(f"  Brands: {len(brands)} seeded")

        vendors = seed_vendors(db, tenant.id)
        print(f"  Vendors: {len(vendors)} seeded")

        customers = seed_customers(db, tenant.id)
        print(f"  Customers: {len(customers)} seeded")

        products = seed_products(db, tenant.id, categories, brands)
        print(f"  Products: {len(products)} seeded")

        warehouses = seed_warehouses(db, tenant.id)
        print(f"  Warehouses: {len(warehouses)} seeded")

        seed_reorder_rules(db, tenant.id, products, warehouses)
        print("  Reorder rules: seeded")

        db.commit()

        stocked = seed_stock(db, tenant.id, admin.id, products, warehouses)
        print(f"  Stock entries: {stocked} seeded across 3 warehouses")
        buffer_stocked = seed_buffer_stock(db, tenant.id, admin.id, products, warehouses)
        print(f"  Workflow stock buffer: {buffer_stocked} idempotent top-up entries applied")

        users_by_role = ensure_role_users(db, tenant.id)
        users_by_role["TENANT_ADMIN"] = admin
        print("  Role users: ensured INVENTORY_MANAGER, SALES_STAFF, PURCHASE_STAFF, VIEWER")

        workflow_summary = seed_workflow_history(
            db,
            tenant.id,
            users_by_role,
            vendors,
            customers,
            products,
            warehouses,
        )
        print(f"  Purchase workflows: {workflow_summary['purchase_orders_seeded']} templates ensured")
        print(f"  Sales workflows: {workflow_summary['sales_orders_seeded']} templates ensured")
        print(f"  Return workflows: {workflow_summary['returns_seeded']} templates ensured")
        print(f"  Cycle count workflows: {workflow_summary['cycle_sessions_seeded']} templates ensured")

        counts = summarize_counts(db, tenant.id)

        print("\nSeed complete!")
        print(f"\n  Tenant: {tenant.company_name}")
        print("  Admin: admin@minimalist.com")
        print("\n  Table totals for tenant 1:")
        for key, value in counts.items():
            print(f"    - {key}: {value}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
