from django.core.mail import EmailMessage
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.validators import validate_email, ValidationError

from io import BytesIO
from picom import settings
from .models import Registration, Player, Sponsorship,Campaign, Submission

import uuid
import json
import qrcode

# Create your views here.
def index(request):
    return render(request, 'register/index.html')

def save_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)   
            billing = data.get('billing', {})       
            submitted = data.get('submitted', {}) 

            # Get player 1 info for Registeration
            with transaction.atomic():
                #first_player = data['players'][0]                
                
                reg = Registration.objects.create(
                    #reg_no=f"REG{Registration.objects.count() + 1:04d},
                    name=billing.get('name', ''),
                    email=billing.get('email', ''),                   
                    address=billing.get('address', ''),
                    comp_reg_no=billing.get('comp_reg_no', ''),
                    campaign_code=billing.get('campaign_id', ''),
                    submitted_by=submitted.get('name', ''),
                    submitted_by_email=submitted.get('email', ''),
                    submitted_by_mobile=submitted.get('mobile', ''),
                )

                #update registrationno
                reg.reg_no = f"REG{reg.id:04d}"                
                reg.save()

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

                #try:
                campaign_code = uuid.UUID(billing.get('campaign_id', ''))

                campaign = Campaign.objects.filter(campaign_code=campaign_code).first()
                if campaign and campaign.pic_email:
                    
                    html_content = render_to_string('register/email/submission_notification.html', {'title': campaign.title, 'url': 'https://pikomgolf.talxone.com/registration_list/89c0dfc3-3d62-49bb-a706-bcbfa6a93cb3/'})
                    valid_emails = []
                    for email in campaign.pic_email.split(','):
                        email = email.strip()
                        try:
                            validate_email(email)
                            valid_emails.append(email)
                        except ValidationError:                            
                            pass
                                    
                    email = EmailMessage(
                        subject='Your day just got better - New Flight Registration!',
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=valid_emails,
                    )
                    email.content_subtype = 'html'
                    email.send()

                #except ValueError:
                    #pass
                
                

            return JsonResponse({'success': True, 'message': 'Registration successful', 'reg_no': reg.reg_no})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def update_registration_remarks(request):
    if request.method == 'POST':
        #print("Updating remarks for registration")
        #print(request.POST.get('registration_code'))
        registration_code = request.POST.get('registration_code')
        remarks = request.POST.get('remarks')

        try:           
            registration_uuid = uuid.UUID(registration_code)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})

        try:
            player = Player.objects.get(registration_code=registration_uuid)
            player.remarks = remarks
           
            player.save()
            return JsonResponse({'status': 'success'})
        except Player.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Player not found'})
        except IntegrityError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Integrity error: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def thankyou(request, reg_no):
    return render(request, 'register/thankyou.html', {'reg_no': reg_no})

def sponsorship(request):
    return render(request, 'register/sponsorship.html')

def save_sponsorship(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) 

            package = data.get('package', None)

            #check if package is already taken
            if package and Sponsorship.objects.filter(package=package).exists():
                return JsonResponse({'success': False, 'code':'1', 'message': 'Package already taken'})
            
            sponsor = Sponsorship.objects.create(
                #reg_no=f"SPN{Sponsorship.objects.count() + 1:04d}",
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
                campaign_code=data.get('campaign_id', ''),
                submitted_by=data.get('submitted_name', ''),
                submitted_by_email=data.get('submitted_email', ''),
                submitted_by_mobile=data.get('submitted_mobile', ''),
            )

            #update sponsorship reg_no
            sponsor.reg_no = f"SPN{sponsor.id:04d}"
            sponsor.save()

            try:
                campaign_code = uuid.UUID(data.get('campaign_id', ''))

                campaign = Campaign.objects.filter(campaign_code=campaign_code).first()
                if campaign and campaign.pic_email:
                   
                    html_content = render_to_string('register/email/sponsorship_notification.html', {'title': campaign.title, 'url': 'https://pikomgolf.talxone.com/sponsorship_list/b251b6c2-f9f6-4634-9a04-d59dd70f743c/'})
                    valid_emails = []
                    for email in campaign.pic_email.split(','):
                        email = email.strip()
                        try:
                            validate_email(email)
                            valid_emails.append(email)
                        except ValidationError:                            
                            pass                    
                    
                    email = EmailMessage(
                        subject='Good news - A New Sponsorship Just Landed!',
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=valid_emails,
                    )
                    email.content_subtype = 'html'
                    email.send()

            except ValueError:
                pass

            return JsonResponse({'success': True, 'code':'0', 'message': 'Sponsorship saved successfully', 'reg_no': sponsor.reg_no})
        except Exception as e:
            return JsonResponse({'success': False, 'code':'2', 'message': str(e)})

    return JsonResponse({'success': False, 'code':'3', 'message': 'Invalid request method'})

def sponsorship_thankyou(request, reg_no):
    return render(request, 'register/sponsorship_thankyou.html', {'reg_no': reg_no})

@login_required
def get_registration_list(request):   

    try:
        if request.method == 'POST':

            campaign_code = request.POST.get('id')  
            campaign_code = campaign_code.replace("-", "")  

            players = Player.objects.select_related('fkregistration').all()
            data = [
                {
                    'reg_no': player.fkregistration.reg_no,
                    'title': player.title,
                    'name': player.name,
                    'email': player.email,
                    'phone': player.mobile,
                    'designation': player.designation,
                    'organization': player.organization,
                    'handicap': player.handicap,
                    'shirt_size': player.tshirt_size,
                    'registration_date': player.fkregistration.created_on.strftime('%Y-%m-%d %H:%M %p'),
                    'remarks': player.remarks if player.remarks else '',
                    'registration_code': str(player.registration_code),
                    'billing_address': player.fkregistration.address,
                    'billing_reg_no': player.fkregistration.comp_reg_no,
                    'billing_email': player.fkregistration.email,
                    'billing_name': player.fkregistration.name,
                    'submitted_by': player.fkregistration.submitted_by,
                    'submitted_by_email': player.fkregistration.submitted_by_email,
                    'submitted_by_mobile': player.fkregistration.submitted_by_mobile,
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
        if request.method == 'POST':

            campaign_code = request.POST.get('id')  
            campaign_code = campaign_code.replace("-", "")  

            sponsorships = Sponsorship.objects.all().order_by('-submitted_at')
            data = []
            for s in sponsorships:
                data.append({
                    'reg_no': s.reg_no,
                    'package': dict(Sponsorship.PACKAGE_CHOICES).get(s.package, s.package),
                    'title': s.title,
                    'name': s.billing_name,
                    'email': s.billing_email,
                    'phone': s.billing_contact,
                    'reg_no': s.billing_reg_no,
                    'organization': s.billing_organization,
                    'address': s.billing_address,
                    'registration_date': s.submitted_at.strftime('%Y-%m-%d %H:%M %p'),
                    'submitted_by': s.submitted_by,
                    'submitted_by_email': s.submitted_by_email,
                    'submitted_by_mobile': s.submitted_by_mobile,
                })
            return JsonResponse(data, safe=False)
    except Sponsorship.DoesNotExist:
        return JsonResponse({'error': 'Sponsorship not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required 
def registration_list(request, id=None):
    current_user = request.user    
    campaign = Campaign.objects.get(campaign_code=id)
    return render(request, 'register/registration_list.html', {'user': current_user, 'campaign': campaign})

@login_required 
def sponsorship_list(request, id=None):
    current_user = request.user    
    campaign = Campaign.objects.get(campaign_code=id)
    return render(request, 'register/sponsorship_list.html', {'user': current_user, 'campaign': campaign})

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

    #print("Creating or updating campaign")

    if request.method == 'POST':
        id = request.POST.get('id')
        title = request.POST.get('title')
        start_date = parse_datetime(request.POST.get('start_date'))
        end_date = parse_datetime(request.POST.get('end_date'))
        is_active = request.POST.get('is_active') == 'true'
        url = request.POST.get('url')
        need_qr = request.POST.get('need_qr') == 'true'
        pic_email = request.POST.get('pic_email', '')
        entry_url = request.POST.get('entry_url', '')
        entry_keyword = request.POST.get('entry_keyword', '')

        if id:
            #print(f"Updating campaign with ID: {id}")
            campaign = get_object_or_404(Campaign, id=id)
            campaign.title = title
            campaign.start_date = start_date
            campaign.end_date = end_date
            campaign.is_active = is_active
            campaign.url = url
            campaign.entry_url = entry_url
            campaign.entry_keyword = entry_keyword
            campaign.need_qr = need_qr
            campaign.pic_email = pic_email
            campaign.save()
        else:
            #print("Creating a new campaign")
            campaign = Campaign.objects.create(
                title=title,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                url=url,
                need_qr=need_qr,
                pic_email=pic_email,
                entry_url=entry_url,
                entry_keyword=entry_keyword
            )
        return JsonResponse({'success': True, 'id': campaign.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_campaign(request, id):
    #print(f"Fetching campaign data for ID: {id}")
    campaign = get_object_or_404(Campaign, id=id)
    data = {
        "title": campaign.title,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else "",
        "end_date": campaign.end_date.isoformat() if campaign.end_date else "",
        "url": campaign.url,
        "active": campaign.is_active,
        "id": campaign.id,
        "need_qr": campaign.need_qr,
        "pic_email": campaign.pic_email,
        "entry_url": campaign.entry_url,
        "entry_keyword": campaign.entry_keyword,
    }
    return JsonResponse(data)

@login_required 
def submission_list(request, id=None):
    #print("Fetching submission list")
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
                    'remarks': s.remarks if s.remarks else '',
                    'is_checked_in': s.is_checked_in,
                })

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_remarks(request):
    if request.method == 'POST':
        #print("Updating remarks for submission")
        reg_no = request.POST.get('reg_no')
        remarks = request.POST.get('remarks')

        try:
            submission = Submission.objects.get(reg_no=reg_no)
            submission.remarks = remarks

            # to ensure submitted_at is not None
            if submission.submitted_at is None:
                submission.submitted_at = timezone.now()

            submission.save()
            return JsonResponse({'status': 'success'})
        except Submission.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Submission not found'})
        except IntegrityError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Integrity error: {str(e)}'
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def check_taken_packages(request):   
    taken_packages = list(Sponsorship.objects.values_list('package', flat=True))
    return JsonResponse({'taken_packages': taken_packages})

def tnc(request):
    current_user = request.user    
    return render(request, 'register/tnc.html', {'user': current_user})

def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue())

def send_qr_email(player, id):
    qr_image = generate_qr_code(str(player.registration_code))   

    if id == "0":
        template_name = 'email_registration.html'
    else:
        template_name = f'email_{id}.html'

    html_content = render_to_string(f'register/email/{template_name}', {'name': player.name})
   
    try:           
        registration_uuid = uuid.UUID(id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})
    
    campaign = get_object_or_404(Campaign, campaign_code=registration_uuid)

   
    if not player.email:
        return False
    
    email = EmailMessage(
        subject='Your Admission QR Code for ' + campaign.title,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[player.email],
    )
    email.content_subtype = 'html'
    email.attach(f'qr_{player.name}.png', qr_image.read(), 'image/png')
   
    try:
        email.send()
        player.qr_sent = True
        player.save()
        return True
    except Exception as e:        
        return False    

def send_qr(request, id):
    if id == "0":
        players = Player.objects.filter(qr_sent=False)
    else:
        id = id.replace("-", "")
        players = Submission.objects.filter(qr_sent=False, campaign_code=id)

    total_sent = 0
    total_players = players.count()
    for player in players:
        if send_qr_email(player, id):
            total_sent += 1

    return HttpResponse(f"QR codes sent successfully to {total_sent} out of {total_players} players.")

def talentgap2025_form(request):
    return render(request, 'register/talentgap2025.html')

def save_submission(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)   

            keyword = data.get('keyword', '').strip()

            campaign = Campaign.objects.filter(entry_keyword__iexact=keyword, is_active=True).first()
            c_id = campaign.campaign_code if campaign else None            

            member = data.get('is_member')
           
            if member and member == 'Yes':
                is_member = True
            else:
                is_member = False

            #convert uuid to string
            c_id = str(c_id)

            reg = Submission.objects.create(
                
                name=data.get('name', ''),
                organization=data.get('organization', ''),
                email=data.get('email', ''),
                mobile=data.get('phone', ''),
                job_title=data.get('designation', ''),
                is_member=is_member,
                campaign_code=c_id.replace("-", "")  ,
                fkcampaign=campaign

            )

            #update registrationno
            reg.reg_no = f"REG{reg.id:06d}"                
            reg.save()

            
            try:
                #campaign_code = c_id

                #campaign = Campaign.objects.filter(campaign_code=campaign_code).first()
                if campaign and campaign.pic_email:
                    
                    html_content = render_to_string('register/email/submission_notification.html', {'title': campaign.title, 'url': 'https://pikomgolf.talxone.com/submission_list/' + c_id.replace("-", "") + '/'})
                    valid_emails = []
                    for email in campaign.pic_email.split(','):
                        email = email.strip()
                        try:
                            validate_email(email)
                            valid_emails.append(email)
                        except ValidationError:                            
                            pass
                                    
                    email = EmailMessage(
                        subject='Your day just got better - New Flight Registration!',
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=valid_emails,
                    )
                    email.content_subtype = 'html'
                    email.send()

            except ValueError:
                pass
            
                

            return JsonResponse({'success': True, 'message': 'Registration successful', 'reg_no': reg.reg_no})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def submission_thankyou(request, reg_no):
    return render(request, 'register/submission_thankyou.html', {'reg_no': reg_no})
