from django.contrib.admin import AdminSite


class PetAdoteAdminSite(AdminSite):
    site_header = 'Administração PetAdote'
    site_title = 'PetAdote Admin'
    index_title = 'Gerenciamento do sistema'
