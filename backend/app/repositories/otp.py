from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.communication import OTPPurpose, OTPSource, OTPVerification


def _utcnow() -> datetime:
    return datetime.now(UTC)


class OTPRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, values: dict) -> OTPVerification:
        otp = OTPVerification(**values)
        self.db.add(otp)
        self.db.flush()
        return otp

    def get_active_by_user_and_purpose(self, user_id: int, purpose: OTPPurpose, destination_type: OTPSource) -> OTPVerification | None:
        now = _utcnow()
        return self.db.scalar(
            select(OTPVerification)
            .where(
                OTPVerification.user_id == user_id,
                OTPVerification.purpose == purpose,
                OTPVerification.destination_type == destination_type,
                OTPVerification.consumed_at.is_(None),
                OTPVerification.superseded_at.is_(None),
                OTPVerification.expires_at > now,
            )
            .order_by(OTPVerification.created_at.desc())
        )

    def supersede_active_for_user(self, user_id: int, purpose: OTPPurpose, destination_type: OTPSource) -> None:
        now = _utcnow()
        self.db.execute(
            update(OTPVerification)
            .where(
                OTPVerification.user_id == user_id,
                OTPVerification.purpose == purpose,
                OTPVerification.destination_type == destination_type,
                OTPVerification.consumed_at.is_(None),
                OTPVerification.superseded_at.is_(None),
                OTPVerification.expires_at > now,
            )
            .values(superseded_at=now)
        )
        self.db.flush()

    def get_by_id(self, otp_id: int) -> OTPVerification | None:
        return self.db.get(OTPVerification, otp_id)

    def increment_attempt(self, otp_id: int) -> None:
        self.db.execute(update(OTPVerification).where(OTPVerification.id == otp_id).values(attempt_count=OTPVerification.attempt_count + 1))
        self.db.flush()

    def mark_consumed(self, otp_id: int) -> None:
        self.db.execute(
            update(OTPVerification).where(OTPVerification.id == otp_id).values(consumed_at=_utcnow())
        )
        self.db.flush()
