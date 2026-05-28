"""
Seed script for the Minimalist tenant (admin@minimalist.com).
Run from backend/: .venv/bin/python scripts/seed_minimalist.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.auth import User, Tenant, UserRole, UserStatus
from app.models.master_data import (
    Brand, Category, Customer, Product, Vendor,
    Warehouse, WarehouseLocation, LocationType, RecordStatus,
)
from app.models.operations import ReorderRule


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
    for v in vendors:
        existing = db.query(Vendor).filter(Vendor.tenant_id == tenant_id, Vendor.name == v["name"]).first()
        if not existing:
            obj = Vendor(tenant_id=tenant_id, **v)
            db.add(obj)
            db.flush()
            result[v["name"]] = obj.id
        else:
            result[v["name"]] = existing.id
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
    for c in customers:
        existing = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.email == c["email"]).first()
        if not existing:
            obj = Customer(tenant_id=tenant_id, **c)
            db.add(obj)
            db.flush()
            result[c["name"]] = obj.id
        else:
            result[c["name"]] = existing.id
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
    for p in products:
        existing = db.query(Product).filter(Product.tenant_id == tenant_id, Product.sku == p["sku"]).first()
        if not existing:
            obj = Product(tenant_id=tenant_id, **p)
            db.add(obj)
            db.flush()
            result[p["sku"]] = obj.id
        else:
            result[p["sku"]] = existing.id
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
        wh_data["locations"] = locations_data  # restore

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
    for r in rules:
        product_id = products.get(r["sku"])
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
                min_quantity=Decimal(str(r["min_qty"])),
                max_quantity=Decimal(str(r["max_qty"])),
                safety_stock=Decimal(str(r["safety"])),
                is_active=True,
            )
            db.add(rule)


def seed_stock(db: Session, tenant_id: int, admin_id: int, products: dict, warehouses: dict):
    from app.services.inventory import InventoryService
    import uuid

    svc = InventoryService(db)
    mum = warehouses["MUM-CW"]
    blr = warehouses["BLR-DH"]
    delhi = warehouses["DEL-FC"]

    stock_plan = [
        # Mumbai Central — main storage
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
        # Bengaluru Hub — partial stock
        {"sku": "MIN-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 800},
        {"sku": "MIN-FC-002", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1200},
        {"sku": "MIN-BC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1500},
        {"sku": "MAM-HC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 600},
        {"sku": "MCA-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 500},
        {"sku": "HIM-FC-001", "wh": blr, "loc_code": "BLR-STR-M", "qty": 1000},
        # Delhi NCR — partial stock
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
            svc.stock_in(tenant_id, admin_id, {
                "product_id": product_id,
                "warehouse_id": wh["id"],
                "location_id": loc_id,
                "quantity": str(entry["qty"]),
                "idempotency_key": idempotency_key,
            })
            stocked += 1
        except Exception:
            pass  # idempotency key already used — skip
    return stocked


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

        print("\nSeed complete!")
        print(f"\n  Tenant: {tenant.company_name}")
        print(f"  Admin: admin@minimalist.com")
        print(f"  Products: {len(products)}")
        print(f"  Warehouses: {len(warehouses)} with {sum(len(w['locations']) for w in warehouses.values())} locations")
        print(f"  Vendors: {len(vendors)}")
        print(f"  Customers: {len(customers)}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
