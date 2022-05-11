from django.contrib import admin
from .models import (
    Game,
    Card,
    Player,
    Players,
    Board,
    Available,
    Used,
    Betcard
)

admin.site.register(Game)
admin.site.register(Card)
admin.site.register(Player)
admin.site.register(Players)
admin.site.register(Board)
admin.site.register(Available)
admin.site.register(Used)
admin.site.register(Betcard)
