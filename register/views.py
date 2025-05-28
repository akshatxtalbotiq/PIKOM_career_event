from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Registration, Player, Sponsorship
import json
from django.db import transaction
from django.contrib.auth.decorators import login_required


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

def sponsorship(request):
    return render(request, 'register/sponsorship.html')

def save_sponsorship(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) 
            
            sponsor = Sponsorship.objects.create(
                reg_no=f"SPN{Sponsorship.objects.count() + 1:04d}",
                title=data['title'],
                contact_name=data['contact_name'],
                contact_number=data['contact_number'],
                contact_email=data['contact_email'],
                billing_organization=data['billing_organization'],
                billing_name=data['billing_name'],
                billing_email=data['billing_email'],
                billing_designation=data['billing_designation'],
                billing_address=data['billing_address'],                
                package=data['package'],  
            )

            return JsonResponse({'success': True, 'message': 'Sponsorship saved successfully', 'reg_no': sponsor.reg_no})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def sponsorship_thankyou(request, reg_no):
    return render(request, 'register/sponsorship_thankyou.html', {'reg_no': reg_no})

@login_required
def get_registration_list(request):   

    try:
        if request.method == 'GET':
            players = Player.objects.select_related('fkregistration').all()
            data = [
                {
                    'reg_no': player.fkregistration.reg_no,
                    'name': f"{player.title} {player.name}",
                    'email': player.email,
                    'phone': player.mobile,
                    'designation': player.designation,
                    'organization': player.organization,
                    'handicap': player.handicap,
                    'shirt_size': player.tshirt_size,
                    'registration_date': player.fkregistration.created_on.strftime('%Y-%m-%d %H:%M %p'),
                }
                for player in players
            ]
        
        
            return JsonResponse(data, safe=False)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Submission not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)   
    
@login_required
def get_sponsorship_list(request):   

    try:
        if request.method == 'GET':
            sponsorships = Sponsorship.objects.all().order_by('-submitted_at')
            data = []
            for s in sponsorships:
                data.append({
                    'reg_no': s.reg_no,
                    'package': dict(Sponsorship.PACKAGE_CHOICES).get(s.package, s.package),
                    'name': f"{s.title} {s.contact_name}",
                    'email': s.contact_email,
                    'phone': s.contact_number,
                    'designation': s.billing_designation,
                    'organization': s.billing_organization,
                    'registration_date': s.submitted_at.strftime('%Y-%m-%d %H:%M %p'),
                })
            return JsonResponse(data, safe=False)
    except Sponsorship.DoesNotExist:
        return JsonResponse({'error': 'Sponsorship not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required 
def registration_list(request):
    current_user = request.user    
    return render(request, 'register/registration_list.html', {'user': current_user})

@login_required 
def sponsorship_list(request):
    current_user = request.user    
    return render(request, 'register/sponsorship_list.html', {'user': current_user})

@login_required
def campaign_list(request):    
    current_user = request.user    
    #get registration and sponsorship count
    registration_count = Registration.objects.count()
    sponsorship_count = Sponsorship.objects.count()

    return render(request, 'register/campaign_list.html', {'user': current_user, 'registration_count': registration_count, 'sponsorship_count': sponsorship_count})


def tnc(request):
    current_user = request.user    
    return render(request, 'register/tnc.html', {'user': current_user})