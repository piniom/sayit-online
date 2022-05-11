from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'game/index.html')

@login_required
def room(request, room_name):
    return render(request, 'game/room.html', {
        'room_name': room_name
    })