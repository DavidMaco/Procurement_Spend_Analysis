"""Role-based access control (RBAC) baseline for the FMCG OS.

Implements a simple but extensible permission model with roles, permissions,
and user-role assignments. Designed to be replaced by a full IAM/SSO provider
in later milestones while preserving the same interface.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Permission(str, Enum):
    """Granular permissions for the FMCG OS."""

    # Read
    VIEW_COMMERCIAL_DASHBOARD = "view:commercial_dashboard"
    VIEW_PROCUREMENT_DASHBOARD = "view:procurement_dashboard"
    VIEW_KPI_CATALOG = "view:kpi_catalog"
    VIEW_ALERTS = "view:alerts"
    VIEW_EVENT_LOG = "view:event_log"

    # Write
    UPLOAD_DATA = "write:upload_data"
    APPROVE_RECOMMENDATION = "write:approve_recommendation"
    REJECT_RECOMMENDATION = "write:reject_recommendation"
    MANAGE_RULES = "write:manage_rules"

    # Admin
    MANAGE_USERS = "admin:manage_users"
    MANAGE_ROLES = "admin:manage_roles"
    VIEW_AUDIT_LOG = "admin:view_audit_log"


class Role(BaseModel):
    """Named set of permissions."""

    name: str
    permissions: frozenset[Permission]
    description: str = ""

    model_config = {"frozen": True}


class User(BaseModel):
    """Minimal user identity with role assignments."""

    user_id: str
    display_name: str
    roles: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# Pre-defined roles
# ---------------------------------------------------------------------------

ROLE_VIEWER = Role(
    name="viewer",
    permissions=frozenset({
        Permission.VIEW_COMMERCIAL_DASHBOARD,
        Permission.VIEW_PROCUREMENT_DASHBOARD,
        Permission.VIEW_KPI_CATALOG,
        Permission.VIEW_ALERTS,
    }),
    description="Read-only access to dashboards and KPIs",
)

ROLE_ANALYST = Role(
    name="analyst",
    permissions=frozenset({
        Permission.VIEW_COMMERCIAL_DASHBOARD,
        Permission.VIEW_PROCUREMENT_DASHBOARD,
        Permission.VIEW_KPI_CATALOG,
        Permission.VIEW_ALERTS,
        Permission.VIEW_EVENT_LOG,
        Permission.UPLOAD_DATA,
    }),
    description="Viewer + data upload and event log access",
)

ROLE_APPROVER = Role(
    name="approver",
    permissions=frozenset({
        Permission.VIEW_COMMERCIAL_DASHBOARD,
        Permission.VIEW_PROCUREMENT_DASHBOARD,
        Permission.VIEW_KPI_CATALOG,
        Permission.VIEW_ALERTS,
        Permission.VIEW_EVENT_LOG,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
    }),
    description="Can approve or reject recommendations",
)

ROLE_ADMIN = Role(
    name="admin",
    permissions=frozenset(Permission),
    description="Full access including user and role management",
)

DEFAULT_ROLES = {
    r.name: r for r in [ROLE_VIEWER, ROLE_ANALYST, ROLE_APPROVER, ROLE_ADMIN]
}


def build_scoped_access_control(
    user_id: str,
    role_names: list[str],
    display_name: Optional[str] = None,
) -> "AccessControlService":
    """Build a request-scoped RBAC service for a single authenticated principal."""
    service = AccessControlService()
    service.add_user(
        User(
            user_id=user_id,
            display_name=display_name or user_id,
            roles=[],
        )
    )
    for role_name in role_names:
        service.assign_role(user_id, role_name)
    return service


# ---------------------------------------------------------------------------
# Access-control service
# ---------------------------------------------------------------------------

class AccessControlService:
    """In-memory RBAC registry.

    Provides ``check_permission`` for use as a guard in API endpoints and
    dashboard pages.
    """

    def __init__(self) -> None:
        self._roles: dict[str, Role] = dict(DEFAULT_ROLES)
        self._users: dict[str, User] = {}

    # -- Role management ---------------------------------------------------

    def add_role(self, role: Role) -> None:
        self._roles[role.name] = role

    def get_role(self, name: str) -> Role:
        if name not in self._roles:
            raise KeyError(f"Role '{name}' not found")
        return self._roles[name]

    def list_roles(self) -> list[Role]:
        return list(self._roles.values())

    # -- User management ---------------------------------------------------

    def add_user(self, user: User) -> None:
        self._users[user.user_id] = user

    def get_user(self, user_id: str) -> User:
        if user_id not in self._users:
            raise KeyError(f"User '{user_id}' not found")
        return self._users[user_id]

    def assign_role(self, user_id: str, role_name: str) -> User:
        user = self.get_user(user_id)
        if role_name not in self._roles:
            raise KeyError(f"Role '{role_name}' not found")
        if role_name in user.roles:
            return user
        updated = User(
            user_id=user.user_id,
            display_name=user.display_name,
            roles=[*user.roles, role_name],
        )
        self._users[user_id] = updated
        return updated

    # -- Permission checks -------------------------------------------------

    def get_user_permissions(self, user_id: str) -> frozenset[Permission]:
        """Aggregate all permissions from all roles assigned to a user."""
        user = self.get_user(user_id)
        perms: set[Permission] = set()
        for rname in user.roles:
            role = self._roles.get(rname)
            if role:
                perms.update(role.permissions)
        return frozenset(perms)

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Return ``True`` if *user_id* holds *permission* via any assigned role."""
        return permission in self.get_user_permissions(user_id)

    def require_permission(self, user_id: str, permission: Permission) -> None:
        """Raise ``PermissionError`` if the check fails."""
        if not self.check_permission(user_id, permission):
            raise PermissionError(
                f"User '{user_id}' lacks permission '{permission.value}'"
            )
