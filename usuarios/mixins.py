from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Usuario


class ClienteRequiredMixin(LoginRequiredMixin):
    """Restringe uma view a clientes com as permissões solicitadas."""

    permission_required = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.perfil != Usuario.Perfil.CLIENTE:
            raise PermissionDenied('Esta área é exclusiva para clientes.')
        if self.permission_required and not request.user.has_perms(self.permission_required):
            raise PermissionDenied('Você não possui permissão para acessar esta página.')
        return super().dispatch(request, *args, **kwargs)


class ConsultaPortalMixin(LoginRequiredMixin):
    """Permite consultas do portal a clientes e administradores autorizados."""

    permission_required = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.permission_required and not request.user.has_perms(self.permission_required):
            raise PermissionDenied('Você não possui permissão para acessar esta página.')
        return super().dispatch(request, *args, **kwargs)
