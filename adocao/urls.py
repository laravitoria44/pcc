from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('vacinacao/', views.vacinacao, name='vacinacao'),
    path('quero-adotar/', views.quero_adotar, name='quero_adotar'),
    path('contato/', views.contato, name='contato'),
]
