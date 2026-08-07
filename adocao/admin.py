from django.contrib import admin
from .models import Contato

@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'assunto', 'data_envio')
    search_fields = ('nome', 'email', 'assunto')
    list_filter = ('data_envio', 'assunto')