from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Registration, Player
import json
from django.db import transaction


# Create your views here.
def index(request):
    return render(request, 'register/index.html')

def save_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)           

            # Get player 1 info for Registeration
            with transaction.atomic():
                first_player = data['players'][0]
                reg = Registration.objects.create(
                    reg_no=f"REG{Registration.objects.count() + 1:04d}",
                    name=first_player['name'],
                    email=first_player['email'],
                    mobile=first_player['mobile']
                )

                # Save all players
                for player in data['players']:
                    Player.objects.create(
                        fkregistration=reg,
                        title=player['title'],
                        name=player['name'],
                        email=player['email'],
                        mobile=player['mobile'],
                        designation=player.get('designation', ''),
                        organization=player.get('organization', ''),
                        handicap=player.get('handicap', ''),
                        tshirt_size=player['tshirt']
                    )

            return JsonResponse({'success': True, 'message': 'Registration successful', 'reg_no': reg.reg_no})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def thankyou(request, reg_no):
    return render(request, 'register/thankyou.html', {'reg_no': reg_no})