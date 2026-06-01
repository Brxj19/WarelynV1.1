from fastapi import APIRouter

from app.api.assistant import router as assistant_router
from app.api.admin import router as admin_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.cycle_counts import router as cycle_counts_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.fulfillment import router as fulfillment_router
from app.api.imports import router as imports_router
from app.api.inventory import router as inventory_router
from app.api.notifications import router as notifications_router
from app.api.purchasing import router as purchasing_router
from app.api.putaway import router as putaway_router
from app.api.reorder_rules import router as reorder_rules_router
from app.api.reports import router as reports_router
from app.api.returns import router as returns_router
from app.api.sales import router as sales_router
from app.api.search import router as search_router
from app.api.settings import router as settings_router
from app.api.uploads import router as uploads_router
from app.api.users import router as users_router
from app.api.verification import router as verification_router
from app.api.warehouses import router as warehouses_router
from app.api.workflow import router as workflow_router

api_router = APIRouter()
api_router.include_router(assistant_router)
api_router.include_router(admin_router)
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(cycle_counts_router)
api_router.include_router(documents_router)
api_router.include_router(health_router)
api_router.include_router(fulfillment_router)
api_router.include_router(imports_router)
api_router.include_router(inventory_router)
api_router.include_router(notifications_router)
api_router.include_router(purchasing_router)
api_router.include_router(putaway_router)
api_router.include_router(reorder_rules_router)
api_router.include_router(reports_router)
api_router.include_router(returns_router)
api_router.include_router(sales_router)
api_router.include_router(search_router)
api_router.include_router(settings_router)
api_router.include_router(uploads_router)
api_router.include_router(users_router)
api_router.include_router(verification_router)
api_router.include_router(warehouses_router)
api_router.include_router(workflow_router)
