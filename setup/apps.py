from django.contrib.admin.apps import AdminConfig


class PetAdoteAdminConfig(AdminConfig):
    default_site = 'setup.admin.PetAdoteAdminSite'
