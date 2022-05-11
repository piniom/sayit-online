from django.shortcuts import render
from django.db import models
from annoying.fields import AutoOneToOneField
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import (
    Card,
    Game,
    Player,
    Board,
    Players,
    Available,
    Used,
    Betcard
)


class GameListView(ListView):
    model = Game
    context_object_name = 'games'
    ordering = ['-date_created']


class GameDetailView(DetailView):
    model = Game


def draw_card(user, cur_game):
    player = Player.objects.get(user=user, game=cur_game)
    if len(cur_game.available.cards.all()) <= 0:
        return False
    if len(player.hand_cards.all()) < 2:
        new_card = cur_game.available.cards.order_by("?").first()
        player.hand_cards.add(new_card)
        cur_game.available.cards.remove(new_card)
        # card_to_remove = Card.objects.filter(id=new_card.id).first()
        # remove_from = Available.objects.filter(game_id=cur_game.id).first().cards
        # remove_from.remove(card_to_remove)
        return True
    return False


def draw_cards(user, cur_game):
    while draw_card(user, cur_game):
        pass


def fill_available(cur_game):
    if len(cur_game.available.cards.all()) <= 0:
        if len(cur_game.used.cards.all()) <= 0:
            for card in Card.objects.all():
                cur_game.available.cards.add(card)
        else:
            for card in cur_game.used.cards.all():
                cur_game.available.cards.add(card)
                cur_game.used.cards.remove(card)


def next_state(request, cur_game):
    users = cur_game.players.users.all()
    messages.add_message(request, messages.SUCCESS, f'Users {users} checked')
    for user in users:
        if Player.objects.filter(user=user.id, game=cur_game.id).first():
            player = Player.objects.get(user=user.id, game=cur_game.id)
            messages.add_message(request,
                                 messages.SUCCESS,
                                 f'User {user} is on state {player.state}')
        else:
            messages.add_message(request, messages.ERROR, f'Player for {user} does not exist')
            return False
    return True


def reset_players_states(request, cur_game):
    users = cur_game.players.users.all()
    messages.add_message(request, messages.SUCCESS, f'Users {users} checked')
    for user in users:
        if Player.objects.filter(user=user.id, game=cur_game.id).first():
            player = Player.objects.get(user=user.id, game=cur_game.id)
            player.state = 0
            player.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 f'User {user} is reset {player.state}')
        else:
            messages.add_message(request, messages.ERROR, f'Player for {user} does not exist(reset)')
            return False
    return True


def game(request):
    if request.method == 'POST':
        game_id = request.POST.get("game_id")
    cur_game = Game.objects.filter(id=game_id).first()
    is_joining = request.POST.get("is_joining")
    player_card = request.POST.get("player_card")
    if player_card:
        player_card = Card.objects.get(id=player_card)
    board_card = request.POST.get("board_card")
    if board_card:
        board_card = Card.objects.get(id=board_card)

    fill_available(cur_game)
    if is_joining == "true":
        # fill_available(cur_game)
        if request.user not in cur_game.players.users.all():
            cur_game.players.users.add(request.user.id)
            # adds the user to the game
            new_player = Player(user=request.user, game=cur_game)
            new_player.save()
            # new_player.hand_cards.set(cur_game.available.cards.order_by("?").all()[:5])
            # cur_game.available.cards.(new_player.hand_cards.first())
            # creates the player connected to the game and the user
    player = Player.objects.filter(user=request.user, game=cur_game).first()
    if player_card:
        if cur_game.board:
            helpin = cur_game.board.game
        cur_game.board.cards.add(player_card.id)
        messages.add_message(request, messages.INFO, f'Karta: {player_card.id}')
        # player.hand_cards.remove(player_card)
        player.state = 1
    elif board_card:
        player.state = 2
        cur_game.used.cards.add(board_card)
        cur_game.board.cards.remove(board_card)
    player.save()
    if next_state(request, cur_game):
        messages.add_message(request, messages.INFO, 'Next State')
        cur_game.state += 1
        if cur_game.state > 3:
            cur_game.state = 0
            reset_players_states(request, cur_game)
        cur_game.save()
    draw_cards(request.user, cur_game)
    context = {
        'game': cur_game,
        'player': player
    }
    #if cur_game.state == 0 and player.state == 0:
       # return render(request, 'dixit/game_stage_0.html', context)

    title = cur_game.betcard.text

    context = {
        'board': cur_game.board.cards.all(),
        'id': cur_game.id,
        'title': cur_game.title,
        'state': cur_game.state,
        'players': cur_game.players.users.all(),
        'player': player,
        'player_state': player.state,
        'player_card': player_card,
        'available': cur_game.available.cards.all(),
        'used': cur_game.used.cards.all(),
        'descrip': title
    }
    return render(request, 'dixit/game.html', context)

