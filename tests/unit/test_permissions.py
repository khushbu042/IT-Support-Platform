import pytest

from app.core.permissions import Permission, ROLE_PERMISSIONS


def test_customer_can_create_and_update_own_ticket():
    customer_permissions = ROLE_PERMISSIONS["customer"]

    assert Permission.TICKET_CREATE in customer_permissions
    assert Permission.TICKET_UPDATE_OWN in customer_permissions
    assert Permission.TICKET_DELETE not in customer_permissions

@pytest.mark.parametrize("role", ["agent", "admin"])
def test_staff_roles_can_read_all_tickets(role):
    assert Permission.TICKET_READ_ALL in ROLE_PERMISSIONS[role]


def test_admin_has_every_permission():
    assert ROLE_PERMISSIONS["admin"] == set(Permission)