from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
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
        return self._commit(self.products.create_for_tenant(tenant_id, values))

    def update_product(self, tenant_id: int, record_id: int, values: dict[str, Any]) -> Product:
        self._validate_product_refs(tenant_id, values)
        return self._update(self.products, tenant_id, record_id, values)

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
