from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """
    Permite acesso somente ao dono do recurso.
    """
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'owner', None)
        if owner is None and hasattr(obj, 'event'):
            owner = getattr(obj.event, 'owner', None)
        if request.method in SAFE_METHODS:
            return owner == request.user
        return owner == request.user