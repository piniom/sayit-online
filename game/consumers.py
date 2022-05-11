import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import random
import os

num_of_cards = 224
num_of_hand_cards = 6
points_for_describing = 3
points_for_guessing = 2
points_for_vote = 1

def save_game(self, data):
    with open('database/game_files/' + self.room_group_name + '_game.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

def open_game(self):
    with open('database/game_files/' + self.room_group_name + '_game.json') as infile:
        return json.load(infile)

def draw_card(self):
    user = self.scope['user']
    game_data = open_game(self)
    for player in game_data['players']:
        if player['user'] == user.id:
            if len(player['cards']) < num_of_hand_cards:
                if len(game_data['game']['available_cards']) <= 0:
                    print('reshuffle')
                    for card in game_data['game']['discarded_cards']:
                        game_data['game']['available_cards'].append(card)
                    game_data['game']['discarded_cards'] = []
                    random.shuffle(game_data['game']['available_cards'])

                new_card = game_data['game']['available_cards'].pop()
                player['cards'].append(new_card)
                
                save_game(self, game_data)
                self.send(text_data=json.dumps({
                    "mode": "draw_card",
                    "card": new_card,
                }))
                return True
            else:
                return False
    return False

def draw_cards(self):
    while draw_card(self):
        pass

def get_player(self, id):
    game_data = open_game(self)
    for cur_player in game_data['players']:
        if cur_player['user'] == id:
            return cur_player

def create_game(self):
        
    #create game
    new_game = {}
    new_game['game'] = {}
    new_game['game']['discarded_cards'] = []
    new_game['game']['state'] = 0
    new_game['game']['describing_player'] = None
    new_game['game']['describing_player_name'] = None
    new_game['game']['describing_player_image_url'] = None
    new_game['game']['description'] = None
    new_game['game']['described_card'] = None
    new_game['game']['board_cards'] = []
    new_game['players'] = []
    cards = []
    for i in range(num_of_cards):
        cards.append(i)
    random.shuffle(cards)
    new_game['game']['available_cards'] = cards
    save_game(self, new_game)
    print(f'New game: {self.room_group_name}')

def player_is_joined(self):
    game_data = open_game(self)
    user = self.scope['user']
    for player in game_data['players']:
        if player['user'] == user.id:
            return True
    print('new player')
    return False

def add_player(self):
    cur_user = self.scope['user']
    head, tail = os.path.split(cur_user.profile.image.path)
    image_url = '/media/profile_pics/' + tail
    new_player = {
        'user': cur_user.id,
        'is_active': False,
        'cards': [],
        'state': 0,
        'points': 0,
        'name': str(cur_user),
        'image_url': image_url,
    }
    game_data = open_game(self)
    players = game_data['players']
    players.append(new_player)
    save_game(self, game_data)
    draw_cards(self)
    print('new player added')

def activate_player(self):
    cur_user = self.scope['user']
    game_data = open_game(self)
    for player in game_data['players']:
        if player['user'] == cur_user.id:
            player['is_active'] = True
            head, tail = os.path.split(cur_user.profile.image.path)
            image_url = '/media/profile_pics/' + tail
            player['image_url'] = image_url
            if player['state'] < game_data['game']['state']:
                player['state'] = game_data['game']['state']
            save_game(self, game_data)
            self.send(text_data=json.dumps({
                "mode": "player_state",
                "state": player['state']
            }))
            break
    save_game(self, game_data)
    send_active_players(self)


def deactivate_player(self):
    cur_user = self.scope['user']
    game_data = open_game(self)
    for player in game_data['players']:
        if player['user'] == cur_user.id:
            player['is_active'] = False
            save_game(self, game_data)
    save_game(self, game_data)
    send_active_players(self)

def send_active_players(self):
    game_data = open_game(self)
    active_players = []
    active_players_names = []
    active_players_points = []
    active_players_images = []
    active_players_states = []
    for player in game_data['players']:
        if player['is_active']:
            active_players.append(player['user'])
            active_players_names.append(player['name'])
            active_players_points.append(player['points'])
            active_players_images.append(player['image_url'])
            active_players_states.append(player['state'])
    save_game(self, game_data)
    output = {
        "type": 'active_players', 
        "players": active_players,
        "names": active_players_names,
        "points": active_players_points,
        "images": active_players_images,
        "states": active_players_states,
    }
    async_to_sync(self.channel_layer.group_send)(
        self.room_group_name, output
    )

def display_cards(self):
    cur_user = self.scope['user']
    game_data = open_game(self)
    for cur_player in game_data['players']:
        if cur_player['user'] == cur_user.id:
            player = cur_player
    for card in player['cards']:
        self.send(text_data=json.dumps({
            "mode": "draw_card",
            "card": card,
        }))

def display_board_cards(self):
    game_data = open_game(self)
    random.shuffle(game_data['game']['board_cards'])
    for card in game_data['game']['board_cards']:
        output = {
            "type": "new_board_card",
            "card": card['card'],
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, output
        )

def display_board_cards_covered(self):
    game_data = open_game(self)
    for card in game_data['game']['board_cards']:
        self.send(text_data=json.dumps({
            "mode": "new_board_card",
            "card": "covered2"
        }))

def check_if_next_state(self):
    game_data = open_game(self)
    no_of_active_players = 0
    for player in game_data['players']:
        if player['is_active'] == True:
            no_of_active_players +=1
            if player['state'] <= game_data['game']['state']:
                return False
    if no_of_active_players > 1:
        return True
    return False

def send_player_state(self, state):
    self.send(text_data=json.dumps({
        "mode": "player_state",
        "state": state,
    }))

def play_card(self, card):
    cur_user = self.scope['user']
    game_data = open_game(self)
    for cur_player in game_data['players']:
        if cur_player['user'] == cur_user.id:
            player = cur_player
    if player['state'] == 0:
        for i, cur_card in enumerate(player['cards']):
            if cur_card == card:
                player['cards'].pop(i)
                game_data['game']['board_cards'].append({
                    'card': card,
                    'user': cur_user.id,
                    'user_name': player['name'],
                    'user_img': player['image_url'] ,
                    'voters': [],
                })
                break
        
        player['state'] = 1
        
        output = {
            "type": "new_board_card_coverd",
            "card": 'covered2',
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, output
        )
        send_player_state(self, 1)
        save_game(self, game_data)
        if check_if_next_state(self):
            game_data['game']['state'] = 1
            save_game(self, game_data)
            output = {
                "type": "new_game_state",
                "state": 1,
            }
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, output
            )
            display_board_cards(self)
        else:
            output = {
                "type": "player_is_done",
                "player": player['user'],
            }
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, output
            )
        draw_cards(self)

def new_describing_player(self):
    game_data = open_game(self)
    if not game_data['game']['describing_player']:
        game_data['game']['describing_player'] = game_data['players'][0]['user']
        user = game_data['players'][0]
    else:
        next_player = False
        for player in game_data['players']:
            if player['is_active']:
                if next_player:
                    next_player = False
                    game_data['game']['describing_player'] = player['user']
                    user = player
                    break
                elif game_data['game']['describing_player'] == player['user']:
                    next_player = True
        if next_player:
            game_data['game']['describing_player'] = game_data['players'][0]['user']
            user = game_data['players'][0]
    
    game_data['game']['describing_player_name'] = user['name']
    game_data['game']['describing_player_image_url'] = user['image_url']
    save_game(self, game_data)
    describing_player = game_data['game']['describing_player']

    print(user['name'])

    output = {
        "type": "new_describing_player",
        "player": describing_player,
        "name": user['name'],
        "image": user['image_url']
    }
    async_to_sync(self.channel_layer.group_send)(
        self.room_group_name, output
    )

def new_description(self, description):
    game_data = open_game(self)
    user = self.scope['user']
    if game_data['game']['state'] == 0 and game_data['game']['describing_player'] == user.id and not game_data['game']['description']:
        game_data['game']['description'] = description
        save_game(self, game_data)
        output = {
            "type": "send_description",
            "description": description,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, output
        )

def described_card(self, card):
    print('described_card')
    user = self.scope['user']
    game_data = open_game(self)
    if game_data['game']['describing_player'] == user.id:
        game_data['game']['described_card'] = card
        save_game(self, game_data)

def end_of_turn(self):
    game_data = open_game(self)
    user = self.scope['user']
    for player in game_data['players']:
        if player['is_active'] == True:
            if player['state'] <= game_data['game']['state'] and game_data['game']['describing_player'] != player['user']:
                return False
    return True

def finish_turn(self):
    print('finish_turn')

    game_data = open_game(self)
    game_data['game']['state'] = 2
    save_game(self, game_data)
    
    output = {
        "type": "finish_turn",
        "card": str(game_data['game']['described_card'])
    }
    async_to_sync(self.channel_layer.group_send)(
        self.room_group_name, output
    )
    other_vote = False
    min_vote = False
    for i, card in enumerate(game_data['game']['board_cards'], start = 0):
        for player in game_data['players']:
            if player['user'] == card['user']:
                cur_player = player
                break
        
        if cur_player['user'] != game_data['game']['describing_player']:
            if len(card['voters']) > 0:
                other_vote = True
                cur_player['points'] += points_for_vote * len(card['voters'])
        else:
            print('desc player')
            if len(card['voters']) > 0:
                min_vote = True
                for voter in card['voters']:
                    for another_player in game_data['players']:
                        if another_player['user'] == voter['user']:
                            print('found a player')
                            another_player['points'] += points_for_guessing
                            break
        output = {
            "type": "card_voters",
            "card": str(card['card']),
            "voters": card['voters'],
            "author": card['user_name'],
            "author_img": card['user_img'],
        }
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, output
        )
    if other_vote and min_vote:
        for player in game_data['players']:
            if player['user'] == game_data['game']['describing_player']:
                player['points'] += points_for_describing
                break
    save_game(self, game_data)
    send_active_players(self)
    

def make_new_turn(self):
    print('new_turn')
    game_data = open_game(self)
    game_data['game']['state'] = 0
    game_data['game']['description'] = None
    game_data['game']['described_card'] = None
    for player in game_data['players']:
        player['state'] = 0
    for card in game_data['game']['board_cards']:
        game_data['game']['discarded_cards'].append(card['card'])
    
    game_data['game']['board_cards'] = []
    save_game(self, game_data)

    output = {
        "type": "new_turn",
    }
    async_to_sync(self.channel_layer.group_send)(
        self.room_group_name, output
    )

    new_describing_player(self)

def card_vote(self, card):
    card = int(card)
    user = self.scope['user']
    game_data = open_game(self)
    for cur_player in game_data['players']:
        if cur_player['user'] == user.id:
            player = cur_player
    if player['state'] == 1:
        for card_data in game_data['game']['board_cards']:
            if card_data['card'] == card and card_data['user'] != user.id:
                voter = {
                    "user": user.id,
                    "user_img": player['image_url'],
                    "user_name": player['name']
                }
                card_data['voters'].append(voter)
                player['state'] = 2
                print(str(player['state']))
                save_game(self, game_data)
                self.send(text_data=json.dumps({
                    "mode": "vote_confirmed",
                    "card": str(card)
                }))
                output = {
                    "type": "player_is_done",
                    "player": player['user'],
                }
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, output
                )
                if(end_of_turn(self)):
                    finish_turn(self)
                break
    

class GameConsumer(WebsocketConsumer):
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

        try:
            with open('database/messages/' + self.room_group_name + '.json') as infile:
                data = json.load(infile)
                for m in data['messages']:
                    self.send(text_data=json.dumps({
                        "mode": "chat",
                        "message": m['message'],
                        "user": m['user'],
                        "userImageUrl": m['userImageUrl'],
                        "userId": m['userId'],
                    }))
        except:
            print(f'New chat: {self.room_group_name}')
        try:
            with open('database/game_files/' + self.room_group_name + '_game.json'):
                if not player_is_joined(self):
                    add_player(self)
                else: 
                    display_cards(self)
                game_data = open_game(self)
                self.send(text_data=json.dumps({
                    "mode": "new_describing_player",
                    "player": game_data['game']['describing_player'],
                    "name": game_data['game']['describing_player_name'],
                    "image": game_data['game']['describing_player_image_url'],
                }))
                if game_data['game']['description']:
                    self.send(text_data=json.dumps({
                        "mode": "new_description",
                        "description": game_data['game']['description'],
                    }))
                print(f'Joining game {self.room_name}')
        except:
            create_game(self)
            add_player(self)
            new_describing_player(self)

        activate_player(self)

        game_data = open_game(self)

        if game_data['game']['state'] == 0:
            display_board_cards_covered(self)

        else:
            global_state = 1 if game_data['game']['state'] == 1 else 2
            self.send(text_data=json.dumps({
                "mode": "new_game_state",
                "state": global_state
            }))
            user = self.scope['user']
            random.shuffle(game_data['game']['board_cards'])
            for player in game_data['players']:
                if player['user'] == user.id:
                    if player['state'] < global_state:
                        player['state'] = global_state
                        send_player_state(self, global_state)
                        save_game(self, game_data)
                        break

            for card in game_data['game']['board_cards']:
                self.send(text_data=json.dumps({
                    "mode": "new_board_card",
                    "card": card['card']
                }))
                if global_state == 2:
                    self.send(text_data=json.dumps({
                        "mode": "card_voters",
                        "card": card['card'],
                        "voters": card['voters'],
                        "author": card['user_name'],
                        "author_img": card['user_img'],
                    }))
                for voter in card['voters']:
                    print('voter found!!!')
                    if user.id == voter:
                        self.send(text_data=json.dumps({
                            "mode": "vote_confirmed",
                            "card": str(card['card'])
                        }))
                    break

            if global_state == 2:
                print('sending description')
                self.send(text_data=json.dumps({
                    "mode": "finish_turn",
                    "card": str(game_data['game']['described_card']),
                    "reload": True,
                }))
           


    def disconnect(self, code):
        game_data = open_game(self)
        # print(str(self.scope['user'].id) + str(game_data['game']['describing_player']))
        # if self.scope['user'].id == game_data['game']['describing_player'] and game_data['game']['state'] == 0:
        #     new_describing_player(self)
        deactivate_player(self)
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        mode = text_data_json['mode']
        if mode == "chat":
            message = text_data_json['message']
            user = text_data_json['user']
            userImageUrl = text_data_json['userImageUrl']
            userId = text_data_json['userId']
            output = {
                    "type": 'chat_message',
                    "message": message,
                    "user": user,
                    "userImageUrl": userImageUrl,
                    "userId": userId,
                }
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, output
            )
            try:
                with open('database/messages/' + self.room_group_name + '.json') as infile:
                    data = json.load(infile)
            except:
                data = {}
                data['messages'] = []

            data['messages'].append(output)
            with open('database/messages/' + self.room_group_name + '.json', 'w') as outfile:
                json.dump(data, outfile, indent=2)
        elif mode == "card_played":
            card = int(text_data_json['card'])
            play_card(self, card)
        elif mode == "new_description":
            description = (text_data_json['description'])
            new_description(self, description)
        elif mode == "card_described":
            print('card described')
            card = (text_data_json['card'])
            described_card(self, card)
        elif mode == "card_vote":
            card = (text_data_json['card'])
            card_vote(self, card)
        elif mode == "next_turn":
            game_data = open_game(self)
            if game_data['game']['state'] == 2:
                make_new_turn(self)

    def chat_message(self, event):
        message = event['message']
        user = event['user']
        userImageUrl = event['userImageUrl']
        userId = event['userId']
        self.send(text_data=json.dumps({
            "mode": "chat",
            "message": message,
            "user": user,
            "userImageUrl": userImageUrl,
            "userId": userId,
        }))

    def active_players(self, event):
        players = event['players']
        names = event['names']
        points = event['points']
        images = event['images']
        states = event['states']
        self.send(text_data=json.dumps({
            "mode": "active_players",
            "players": players,
            "names": names,
            "points": points,
            "images": images,
            "states": states
        }))

    def new_board_card(self, event):
        card = event['card']
        self.send(text_data=json.dumps({
            "mode": "new_board_card",
            "card": card,
        }))

    def new_board_card_coverd(self, event):
        card = event['card']
        self.send(text_data=json.dumps({
            "mode": "new_board_card",
            "card": card,
        }))

    def new_describing_player(self, event):
        player = event['player']
        name = event['name']
        image = event['image']
        print('new describing player: ' + str(player))
        self.send(text_data=json.dumps({
            "mode": "new_describing_player",
            "player": player,
            "name": name,
            "image": image,
        }))

    def new_game_state(self, event):
        state = event['state']
        self.send(text_data=json.dumps({
            "mode": "new_game_state",
            "state": state,
        }))
    
    def send_description(self, event):
        description = event['description']
        self.send(text_data=json.dumps({
            "mode": "new_description",
            "description": description,
        }))

    def card_voters(self, event):
        voters = event['voters']
        card = event['card']
        author = event['author']
        author_img = event['author_img']
        self.send(text_data=json.dumps({
            "mode": "card_voters",
            "card": card,
            "voters": voters,
            "author": author,
            "author_img": author_img,
        }))

    def finish_turn(self, event):
        card = event['card']
        self.send(text_data=json.dumps({
            "mode": "finish_turn",
            "card": card,
        }))

    def new_turn(self, event):
        self.send(text_data=json.dumps({
            "mode": "next_turn",
        }))

    def player_is_done(self, event):
        player = event['player']
        self.send(text_data=json.dumps({
            "mode": "player_is_done",
            "player": player,
        }))
