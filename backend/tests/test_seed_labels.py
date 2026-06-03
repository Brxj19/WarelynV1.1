from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from sqlalchemy import select

from app.models.auth import Tenant
from app.models.inventory import InventoryBatch, InventorySerial
from app.models.master_data import Product
from scripts import seed_dmart

BATCH_PATTERN = re.compile(r"^[A-Z0-9-]+-B\d{3}-MFG\d{4}$")
SERIAL_PATTERN = re.compile(r"^[A-Z0-9]+-SN-\d{5}$")


def test_dmart_seed_labels_are_unique_and_well_formed(db_session) -> None:
    seed_dmart.seed_database(db_session)

    tenant = db_session.scalar(select(Tenant).where(Tenant.company_name == seed_dmart.TENANT_NAME))
    assert tenant is not None

    products = db_session.scalars(select(Product).where(Product.tenant_id == tenant.id)).all()
    products_by_id = {product.id: product for product in products}
    products_by_sku = {product.sku: product for product in products}

    batches = db_session.scalars(select(InventoryBatch).where(InventoryBatch.tenant_id == tenant.id)).all()
    serials = db_session.scalars(select(InventorySerial).where(InventorySerial.tenant_id == tenant.id)).all()

    batch_numbers = [batch.batch_number for batch in batches]
    assert len(batch_numbers) == len(set(batch_numbers))
    assert batch_numbers
    assert all(BATCH_PATTERN.match(batch_number) for batch_number in batch_numbers)

    serial_numbers = [serial.serial_number for serial in serials]
    assert len(serial_numbers) == len(set(serial_numbers))
    assert serial_numbers
    assert all(SERIAL_PATTERN.match(serial_number) for serial_number in serial_numbers)

    batch_tracked_skus = {
        spec["sku"]
        for spec in seed_dmart.PRODUCT_SPECS
        if spec["tracking"] == "BATCH"
    }
    serial_tracked_skus = {
        spec["sku"]
        for spec in seed_dmart.PRODUCT_SPECS
        if spec["tracking"] == "SERIAL"
    }

    assert batch_tracked_skus == {product.sku for product in products if product.track_batch or product.track_expiry}
    assert serial_tracked_skus == {product.sku for product in products if product.track_serial}

    for sku in batch_tracked_skus:
        product = products_by_sku[sku]
        product_batches = [batch.batch_number for batch in batches if batch.product_id == product.id]
        assert len(product_batches) == 3
        assert len(set(product_batches)) == 3

    serials_by_product: dict[int, list[str]] = defaultdict(list)
    for serial in serials:
        serials_by_product[serial.product_id].append(serial.serial_number)

    for sku in serial_tracked_skus:
        product = products_by_sku[sku]
        expected_count = next(sum(spec["receipt_quantities"]) for spec in seed_dmart.PRODUCT_SPECS if spec["sku"] == sku)
        product_serials = serials_by_product[product.id]
        assert len(product_serials) == expected_count
        assert len(set(product_serials)) == expected_count

    amul_milk_batches = [
        batch
        for batch in batches
        if products_by_id[batch.product_id].sku == "FOOD-MILK-AMUL1L"
    ]
    assert any(batch.expiry_date is not None and batch.expiry_date < date.today() for batch in amul_milk_batches)
