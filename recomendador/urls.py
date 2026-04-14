from django.urls import path
from . import views

urlpatterns = [
    path('',          views.index,         name='index'),
    path('result/',   views.result_view,   name='result'),
    path('login/',    views.spotify_login, name='spotify_login'),
    path('callback/', views.callback,      name='callback'),
]