from django.core.mail import EmailMessage
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse, JsonResponse

from picom import settings
from .models import Registration, Player, Sponsorship,Campaign, Submission
import json
from django.db import transaction
from django.contrib.auth.decorators import login_required
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime


# Create your views here.
def index(request):
    return render(request, 'register/index.html')

def save_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)   
            billing = data.get('billing', {})        

            # Get player 1 info for Registeration
            with transaction.atomic():
                #first_player = data['players'][0]
                reg = Registration.objects.create(
                    reg_no=f"REG{Registration.objects.count() + 1:04d}",
                    name=billing.get('name', ''),
                    email=billing.get('email', ''),                   
                    address=billing.get('address', ''),
                    comp_reg_no=billing.get('comp_reg_no', ''),
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
                #contact_name=data['contact_name'],
                #contact_number=data['contact_number'],
                #contact_email=data['contact_email'],
                billing_name=data['billing_name'],
                billing_organization=data['billing_organization'],
                billing_reg_no=data['billing_reg_no'],
                billing_email=data['billing_email'],
                billing_contact=data['billing_contact'],
                #billing_designation=data['billing_designation'],
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
                    'name': f"{s.title} {s.billing_name}",
                    'email': s.billing_email,
                    'phone': s.billing_contact,
                    'reg_no': s.billing_reg_no,
                    'organization': s.billing_organization,
                    'registration_date': s.submitted_at.strftime('%Y-%m-%d %H:%M %p'),
                })
            return JsonResponse(data, safe=False)
    except Sponsorship.DoesNotExist:
        return JsonResponse({'error': 'Sponsorship not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required 
def registration_list(request, id=None):
    current_user = request.user    
    return render(request, 'register/registration_list.html', {'user': current_user})

@login_required 
def sponsorship_list(request, id=None):
    current_user = request.user    
    return render(request, 'register/sponsorship_list.html', {'user': current_user})

@login_required
def campaign_list(request):    
    current_user = request.user    
    #get registration and sponsorship count
    #registration_count = Registration.objects.count()
    #sponsorship_count = Sponsorship.objects.count()

    campaigns = Campaign.objects.all()

    return render(request, 'register/campaign_list.html', {'user': current_user, 'campaigns': campaigns})

@login_required
def create_campaign(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        title = request.POST.get('title')
        start_date = parse_datetime(request.POST.get('start_date'))
        end_date = parse_datetime(request.POST.get('end_date'))
        is_active = request.POST.get('is_active') == 'true'
        url = request.POST.get('url')

        if id:
            print(f"Updating campaign with ID: {id}")
            campaign = get_object_or_404(Campaign, id=id)
            campaign.title = title
            campaign.start_date = start_date
            campaign.end_date = end_date
            campaign.is_active = is_active
            campaign.url = url
            campaign.save()
        else:
            print("Creating a new campaign")
            campaign = Campaign.objects.create(
                title=title,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                url=url
            )
        return JsonResponse({'success': True, 'id': campaign.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_campaign(request, id):
    print(f"Fetching campaign data for ID: {id}")
    campaign = get_object_or_404(Campaign, id=id)
    data = {
        "title": campaign.title,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else "",
        "end_date": campaign.end_date.isoformat() if campaign.end_date else "",
        "url": campaign.url,
        "active": campaign.is_active,
        "id": campaign.id
    }
    return JsonResponse(data)

@login_required 
def submission_list(request, id=None):
    current_user = request.user    
    campaign = Campaign.objects.get(campaign_code=id)
    return render(request, 'register/submission_list.html', {'user': current_user, 'campaign': campaign})

@login_required
def get_submission_list(request):   
    try:
        if request.method == 'POST':
            campaign_code = request.POST.get('id')  
            campaign_code = campaign_code.replace("-", "")  
            submissions = Submission.objects.filter(campaign_code=campaign_code).order_by('-submitted_at')
            
            data = []
            for s in submissions:
                data.append({
                    'reg_no': s.reg_no,                    
                    'name': s.name,
                    'email': s.email,
                    'job_title': s.job_title,
                    'organization': s.organization,
                    'registration_date': s.submitted_at.strftime('%Y-%m-%d %I:%M %p') if s.submitted_at else '',
                })

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def tnc(request):
    current_user = request.user    
    return render(request, 'register/tnc.html', {'user': current_user})

def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue())

def send_qr_email(player):
    qr_image = generate_qr_code(str(player.registration_code))

    email = EmailMessage(
        'Your Event QR Code',
        f'Dear {player.name}, please find your QR code attached. Use this to check in at the event.',
        settings.DEFAULT_FROM_EMAIL,
        [player.email]
    )
    email.attach(f'qr_{player.name}.png', qr_image.read(), 'image/png')
    try:
        email.send()
        player.qr_sent = True
        player.save()
        return True
    except Exception as e:        
        return False    

def send_qr(request):
    players = Player.objects.filter(qr_sent=False)
    for player in players:
        send_qr_email(player)