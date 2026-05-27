from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.operations import ReorderRuleCreate, ReorderRuleRead, ReorderRuleUpdate
from app.services.auth import UserContext
from app.services.operations import ReorderRuleService

router = APIRouter(prefix="/reorder-rules", tags=["reorder-rules"])
roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=list[ReorderRuleRead])
def list_reorder_rules(context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return ReorderRuleService(db).list(context.tenant_id)


@router.get("/{rule_id}", response_model=ReorderRuleRead)
def get_reorder_rule(rule_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return ReorderRuleService(db).get(context.tenant_id, rule_id)


@router.post("", response_model=ReorderRuleRead, status_code=201)
def create_reorder_rule(body: ReorderRuleCreate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return ReorderRuleService(db).create(context.tenant_id, body.model_dump())


@router.patch("/{rule_id}", response_model=ReorderRuleRead)
def update_reorder_rule(rule_id: int, body: ReorderRuleUpdate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return ReorderRuleService(db).update(context.tenant_id, rule_id, body.model_dump(exclude_unset=True))


@router.delete("/{rule_id}", status_code=204)
def delete_reorder_rule(rule_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    ReorderRuleService(db).delete(context.tenant_id, rule_id)
