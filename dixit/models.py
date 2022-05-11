from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from annoying.fields import AutoOneToOneField
from django.urls import reverse
from PIL import Image


class Card(models.Model):
    image = models.ImageField(default='default.jpg', upload_to='card_pics')


class Game(models.Model):
    title = models.CharField(max_length=100)
    date_created = models.DateTimeField(default=timezone.now)
    description = models.TextField(null=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    state = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    hand_cards = models.ManyToManyField('Card')
    state = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user} in game {self.game}'


class Available(models.Model):
    game = AutoOneToOneField(Game, primary_key=True, on_delete=models.CASCADE)
    cards = models.ManyToManyField('Card')

    def start(self):
        for card in Card.objects.all():
            self.cards.add(card)

    def __str__(self):
        return f'{self.game} Available'


class Used(models.Model):
    game = AutoOneToOneField(Game, primary_key=True, on_delete=models.CASCADE)
    cards = models.ManyToManyField('Card')

    def __str__(self):
        return f'{self.game} Used'


class Board(models.Model):
    game = AutoOneToOneField(Game, primary_key=True, on_delete=models.CASCADE)
    cards = models.ManyToManyField('Card')

    def __str__(self):
        return f'{self.game} Board'


class Players(models.Model):
    game = AutoOneToOneField(Game, primary_key=True, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)

    def __str__(self):
        return f'{self.game} Players'


class Betcard(models.Model):
    text = models.CharField(max_length=100)
    img = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    game = AutoOneToOneField(Game, primary_key=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.game} description'
