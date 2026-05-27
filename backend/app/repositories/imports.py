from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.imports import ImportJob, ImportJobRow, ImportRowStatus
from app.models.master_data import Brand, Category, Product, Vendor


class ImportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, values: dict) -> ImportJob:
        job = ImportJob(**values)
        self.db.add(job)
        self.db.flush()
        return job

    def get_job(self, tenant_id: int, job_id: int) -> ImportJob | None:
        return self.db.scalar(select(ImportJob).where(ImportJob.id == job_id, ImportJob.tenant_id == tenant_id))

    def create_rows(self, rows: list[ImportJobRow]) -> None:
        self.db.add_all(rows)
        self.db.flush()

    def list_rows(self, tenant_id: int, job_id: int) -> list[ImportJobRow]:
        return list(self.db.scalars(select(ImportJobRow).where(ImportJobRow.tenant_id == tenant_id, ImportJobRow.job_id == job_id).order_by(ImportJobRow.row_number)))

    def get_product_by_sku(self, tenant_id: int, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku))

    def get_product_by_barcode(self, tenant_id: int, barcode: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.barcode == barcode))

    def get_category_by_name(self, tenant_id: int, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.tenant_id == tenant_id, Category.name == name))

    def get_brand_by_name(self, tenant_id: int, name: str) -> Brand | None:
        return self.db.scalar(select(Brand).where(Brand.tenant_id == tenant_id, Brand.name == name))

    def get_vendor_by_name(self, tenant_id: int, name: str) -> Vendor | None:
        return self.db.scalar(select(Vendor).where(Vendor.tenant_id == tenant_id, Vendor.name == name))

    def create_category(self, tenant_id: int, name: str) -> Category:
        category = Category(tenant_id=tenant_id, name=name)
        self.db.add(category)
        self.db.flush()
        return category

    def create_brand(self, tenant_id: int, name: str) -> Brand:
        brand = Brand(tenant_id=tenant_id, name=name)
        self.db.add(brand)
        self.db.flush()
        return brand

    def create_vendor(self, tenant_id: int, name: str) -> Vendor:
        vendor = Vendor(tenant_id=tenant_id, name=name)
        self.db.add(vendor)
        self.db.flush()
        return vendor

    def create_product(self, values: dict) -> Product:
        product = Product(**values)
        self.db.add(product)
        self.db.flush()
        return product

    def valid_rows(self, tenant_id: int, job_id: int) -> list[ImportJobRow]:
        return list(self.db.scalars(select(ImportJobRow).where(ImportJobRow.tenant_id == tenant_id, ImportJobRow.job_id == job_id, ImportJobRow.status.in_([ImportRowStatus.VALID, ImportRowStatus.WARNING])).order_by(ImportJobRow.row_number)))
