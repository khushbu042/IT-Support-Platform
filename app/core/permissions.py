from enum import Enum

class Permission(str, Enum):
    TICKET_CREATE = "ticket:create"
    TICKET_READ_OWN = "ticket:read_own"       # customer sees only their own tickets
    TICKET_READ_ALL = "ticket:read_all"       # agent/admin see all tickets
    TICKET_UPDATE_OWN = "ticket:update_own"   # customer can edit their own ticket (e.g. add comment)
    TICKET_UPDATE_ANY = "ticket:update_any"   # agent/admin can update any ticket (status, notes)
    TICKET_DELETE = "ticket:delete"
    TICKET_ASSIGN = "ticket:assign"           # assign ticket to an agent
    USER_MANAGE = "user:manage"               # create/edit/deactivate users

ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "customer": {
        Permission.TICKET_CREATE,
        Permission.TICKET_READ_OWN,
        Permission.TICKET_UPDATE_OWN,
    },
    "agent": {
        Permission.TICKET_READ_ALL,
        Permission.TICKET_UPDATE_ANY,
        Permission.TICKET_ASSIGN,
    },
    "admin": set(Permission),  # full access, including USER_MANAGE and TICKET_DELETE
}