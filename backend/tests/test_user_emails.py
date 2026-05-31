"""Tests for user management email triggers and notifications."""
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.schemas.users import UserCreate, UserUpdate
from app.services.users import UsersService
from app.utils.phone import normalize_phone, validate_phone


def _setup_tenant_and_actor(db: Session) -> tuple[int, int]:
    """Create a tenant and an admin user, return (tenant_id, actor_user_id)."""
    tenant = Tenant(
        company_name="Test Corp",
        contact_email="admin@testcorp.com",
    )
    db.add(tenant)
    db.flush()

    actor = User(
        tenant_id=tenant.id,
        name="Admin User",
        email="admin@testcorp.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(actor)
    db.flush()
    return tenant.id, actor.id


class TestUserEmailTriggers:
    """Test that user operations trigger emails."""

    @patch("app.services.users.send_email")
    def test_create_user_triggers_email(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="New User",
            email="newuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)

        assert user.id is not None
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["to_email"] == "newuser@testcorp.com"

    @patch("app.services.auth.send_password_reset_link_email")
    @patch("app.services.users.send_email")
    def test_password_reset_triggers_email(self, mock_send_email: MagicMock, mock_send_reset_link_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Reset User",
            email="resetuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)
        mock_send_email.reset_mock()
        mock_send_reset_link_email.reset_mock()

        service.reset_password(tenant_id, actor_id, user.id)

        mock_send_email.assert_not_called()
        mock_send_reset_link_email.assert_called_once()
        call_args, call_kwargs = mock_send_reset_link_email.call_args
        if call_kwargs:
            assert call_kwargs["to_email"] == "resetuser@testcorp.com"
        else:
            assert call_args[0] == "resetuser@testcorp.com"

    @patch("app.services.users.send_email")
    def test_disable_user_triggers_email(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Disable User",
            email="disableuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)
        mock_send_email.reset_mock()

        service.disable_user(tenant_id, actor_id, user.id)

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["to_email"] == "disableuser@testcorp.com"

    @patch("app.services.users.send_email")
    def test_enable_user_triggers_email(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Enable User",
            email="enableuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)
        # Disable first
        service.disable_user(tenant_id, actor_id, user.id)
        mock_send_email.reset_mock()

        service.enable_user(tenant_id, actor_id, user.id)

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["to_email"] == "enableuser@testcorp.com"

    @patch("app.services.users.send_email")
    def test_role_changed_triggers_email(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Role User",
            email="roleuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)
        mock_send_email.reset_mock()

        update_data = UserUpdate(role=UserRole.SALES_STAFF)
        service.update_user(tenant_id, actor_id, user.id, update_data)

        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["to_email"] == "roleuser@testcorp.com"

    @patch("app.services.users.send_email")
    def test_email_failure_does_not_rollback_user_operation(self, mock_send_email: MagicMock, db_session: Session):
        """Email failure should not prevent user creation."""
        mock_send_email.side_effect = Exception("SMTP connection failed")
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Fail Email User",
            email="failuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        # Should not raise despite email failure
        user = service.create_user(tenant_id, actor_id, data)

        assert user.id is not None
        assert user.email == "failuser@testcorp.com"


class TestUserNotifications:
    """Test that user operations create notifications."""

    @patch("app.services.users.send_email")
    def test_notifications_created_for_user_events(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Notify User",
            email="notifyuser@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
        )
        user = service.create_user(tenant_id, actor_id, data)

        # Check that notifications were created
        from app.models.communication import Notification
        from sqlalchemy import select

        notifications = list(db_session.scalars(
            select(Notification).where(Notification.user_id == user.id)
        ))
        assert len(notifications) >= 1
        assert any("Account Created" in n.title for n in notifications)


class TestPhoneValidation:
    """Test phone number validation and normalization."""

    def test_normalize_phone_strips_spaces_and_dashes(self):
        assert normalize_phone("+91 98765-43210") == "+919876543210"
        assert normalize_phone("+1 (555) 123-4567") == "+15551234567"

    def test_normalize_phone_adds_plus(self):
        assert normalize_phone("919876543210") == "+919876543210"

    def test_normalize_phone_empty(self):
        assert normalize_phone("") == ""

    def test_validate_phone_empty_is_valid(self):
        valid, error = validate_phone("")
        assert valid is True
        assert error == ""

    def test_validate_phone_invalid_characters(self):
        valid, error = validate_phone("+91abc123")
        assert valid is False
        assert "digits only" in error

    def test_validate_phone_too_short(self):
        valid, error = validate_phone("+1234")
        assert valid is False
        assert "length" in error

    def test_validate_phone_india_valid(self):
        valid, error = validate_phone("+919876543210")
        assert valid is True
        assert error == ""

    def test_validate_phone_india_invalid_length(self):
        valid, error = validate_phone("+9198765")
        assert valid is False
        assert "+91" in error
        assert "10 digits" in error

    def test_validate_phone_us_valid(self):
        valid, error = validate_phone("+15551234567")
        assert valid is True
        assert error == ""

    def test_validate_phone_us_invalid_length(self):
        valid, error = validate_phone("+1555123")
        assert valid is False
        assert "+1" in error
        assert "10 digits" in error

    def test_validate_phone_uk_valid_range(self):
        # UK numbers can be 7-10 digits after +44
        valid, error = validate_phone("+447911123456")
        assert valid is True
        assert error == ""

    @patch("app.services.users.send_email")
    def test_invalid_phone_rejected_on_create(self, mock_send_email: MagicMock, db_session: Session):
        from app.core.exceptions import AppError

        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Bad Phone User",
            email="badphone@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
            phone="+9198765",  # Invalid: too short for India
        )
        with pytest.raises(AppError) as exc_info:
            service.create_user(tenant_id, actor_id, data)
        assert exc_info.value.code == "INVALID_PHONE"

    @patch("app.services.users.send_email")
    def test_valid_phone_accepted_and_normalized(self, mock_send_email: MagicMock, db_session: Session):
        tenant_id, actor_id = _setup_tenant_and_actor(db_session)
        service = UsersService(db_session)

        data = UserCreate(
            name="Good Phone User",
            email="goodphone@testcorp.com",
            role=UserRole.VIEWER,
            password="securepass123",
            phone="+91 98765 43210",
        )
        user = service.create_user(tenant_id, actor_id, data)
        assert user.phone == "+919876543210"
