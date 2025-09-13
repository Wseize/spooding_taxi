from rest_framework.permissions import BasePermission, SAFE_METHODS

class TaxiPermission(BasePermission):
    """
    Admins can do everything.
    Chauffeurs can read/update their own taxi only.
    Others cannot modify.
    """

    def has_permission(self, request, view):
        # Tout le monde peut voir la liste et détails en GET
        if request.method in SAFE_METHODS:
            return True
        # POST, DELETE, etc. : uniquement admin
        return request.user.is_staff or request.user.is_driver

    def has_object_permission(self, request, view, obj):
        # Admin peut tout
        if request.user.is_staff:
            return True
        # Chauffeur propriétaire peut lire et update
        if request.user.is_driver and obj.driver == request.user:
            return request.method in SAFE_METHODS + ('PUT', 'PATCH')
        # Autres : interdit
        return False
