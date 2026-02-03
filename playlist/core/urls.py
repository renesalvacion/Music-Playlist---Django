from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add-music/', views.add_music, name='add_music'),
    path('get-playlist/', views.get_playlist, name='get_playlist'),
    path('delete-music/', views.delete_music, name='delete_music'),
]
