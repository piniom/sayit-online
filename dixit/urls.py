from django.urls import path
from . import views
from .views import (
    GameListView,
    GameDetailView,
    game,
)

urlpatterns = [
    path('', GameListView.as_view(), name='game-list'),
    path('game/<int:pk>/', GameDetailView.as_view(), name='game-detail'),
    path('gameDixit/', game, name='game'),
]