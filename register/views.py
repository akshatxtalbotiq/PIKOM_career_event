from email.utils import formataddr

from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.validators import validate_email, ValidationError
from django.utils.html import strip_tags

from django.contrib.auth.models import User
from io import BytesIO

from urllib3 import request
from picom import settings
from .models import Registration, Player, Sponsorship,Campaign, Submission,CampaignTeam, Survey, Question, Answer, SurveyUser

import uuid
import json
import qrcode

from django.views.decorators.csrf import csrf_exempt

from email.mime.image import MIMEImage
import os



# Create your views here.
def index(request):
    return render(request, 'register/index.html')

def save_registration(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)   
            billing = data.get('billing', {})       
            submitted = data.get('submitted', {}) 

            # Get player 1 info for Registration
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

    users = User.objects.all()
    user_data = [{"id": user.id, "email": user.email, "name": user.get_full_name()} for user in users]

    if current_user.is_superuser:
        # Show all campaigns
        campaigns = Campaign.objects.all()
    else:
        # get list of campign id that has user id in CampaignTeam model
        campaigns = Campaign.objects.filter(campaign_teams__user=current_user).distinct()

    return render(request, 'register/campaign_list.html', {'user': current_user, 'campaigns': campaigns, 'users': user_data})

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
        selected_users = request.POST.getlist("users[]")

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

        #delete the rows for CampaignTeam model
        CampaignTeam.objects.filter(campaign=campaign).delete()

        #save the users in CampaignTeam model
        for user_id in selected_users:
            user = get_object_or_404(User, id=user_id)
            CampaignTeam.objects.create(campaign=campaign, user=user)

        return JsonResponse({'success': True, 'id': campaign.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_campaign(request, id):
    #print(f"Fetching campaign data for ID: {id}")
    campaign = get_object_or_404(Campaign, id=id)

    user = request.user
    
    #get the list of users in auth_user table
    users = User.objects.all()
    user_data = [{"id": user.id, "email": user.email, "name": user.get_full_name()} for user in users] 

    #for the campaign, get the data from CampaignTeam
    selected_users = [team.user.id for team in campaign.campaign_teams.all()]

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
        "users": user_data,
        "selected_users": selected_users
    }
    return JsonResponse(data)

@login_required 
def submission_list(request, id=None):
    #print("Fetching submission list")
    current_user = request.user
    campaign = Campaign.objects.get(campaign_code=id)

    surveyExists = False
    if Survey.objects.filter(fkcampaign=campaign).exists():
        surveyExists = True

    #get html from template register/submission_list_checkin.html and send in the context
    checkin_html = render(request, 'register/submission_list_checkin.html').content.decode('utf-8')

    exclude_columns = campaign.exclude_columns if campaign and campaign.exclude_columns else []
    column_list = [       
        {'data': 'reg_no', 'name': 'Registration No'},
        {'data': 'name', 'name': 'Name'},
        {'data': 'email', 'name': 'Email'},
        {'data': 'mobile', 'name': 'Mobile'},
        {'data': 'organization', 'name': 'Organization'},
        {'data': 'job_title', 'name': 'Job Title'},       
        {'data': 'registration_code', 'name': 'Registration Code'},
        {'data': 'is_checked_in', 'name': 'Checked In'},
        {'data': 'is_qr_sent', 'name': 'QR Sent'},       
        {'data': 'remarks', 'name': 'Remarks'},
        {'data': 'is_member', 'name': 'Is Member'},
        {'data': 'category', 'name': 'Category'},
        {'data': 'promo_code', 'name': 'Promo Code'},       
    ]

    return render(request, 'register/submission_list.html', {'user': current_user, 'campaign': campaign, 'surveyExists': surveyExists, 'checkin_html': checkin_html, 'exclude_columns': exclude_columns, 'column_list': column_list})

@login_required
def get_submission_list(request):   
    try:
        if request.method == 'POST':
            campaign_code = request.POST.get('id')  
            campaign_code = campaign_code.replace("-", "")  
            submissions = Submission.objects.filter(campaign_code=campaign_code).order_by('-submitted_at')
            campaign = Campaign.objects.filter(campaign_code=campaign_code).first()
          

            data = []
            checked_in_count = 0
            total_count = submissions.count()
            for s in submissions:
                data.append({
                    'id': s.id,
                    'reg_no': s.reg_no,
                    'name': s.name,
                    'email': s.email,
                    'mobile': s.mobile if s.mobile else '',
                    'organization': s.organization if s.organization else '',
                    'job_title': s.job_title if s.job_title else '',
                    'registration_date': s.submitted_at.strftime('%Y-%m-%d %I:%M %p') if s.submitted_at else '',
                    'last_modified': s.lastmodified.strftime('%Y-%m-%d %I:%M %p') if s.lastmodified else '',
                    'registration_code': str(s.registration_code),
                    'is_checked_in': s.is_checked_in,
                    'is_qr_sent': s.qr_sent,
                    'campaign_code': s.campaign_code if s.campaign_code else '',
                    'remarks': s.remarks if s.remarks else '',
                    'is_member': s.is_member,
                    'member_code': s.member_code if s.member_code else '',
                    'fkcampaign': s.fkcampaign.id if s.fkcampaign else '',
                    'fkcampaign_name': s.fkcampaign.name if s.fkcampaign and hasattr(s.fkcampaign, 'name') else '',
                    'category': s.category if s.category else '',
                    'promo_code': s.promo_code if s.promo_code else '',
                    'consent': s.consent,
                })

                # data.append({
                #     'id': s.id,
                #     'reg_no': s.reg_no,                    
                #     'name': s.name,
                #     'email': s.email,
                #     'job_title': s.job_title,
                #     'organization': s.organization,
                #     'registration_date': s.submitted_at.strftime('%Y-%m-%d %I:%M %p') if s.submitted_at else '',
                #     'remarks': s.remarks if s.remarks else '',
                #     'is_checked_in': s.is_checked_in,
                #     'is_qr_sent': s.qr_sent,
                # })
                if s.is_checked_in:
                    checked_in_count += 1

            return JsonResponse({
                'data': data,
                'total_count': total_count,
                'checked_in_count': checked_in_count,
                'exclude_columns': campaign.exclude_columns if campaign and campaign.exclude_columns else []
            }, safe=False)
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

def exclude_columns(request):
    if request.method == 'POST':
        campaign_id = request.POST.get('campaign_id')
        exclude_columns = request.POST.getlist('exclude_columns[]')

        try:
            campaign = Campaign.objects.get(id=campaign_id)
            campaign.exclude_columns = json.dumps(exclude_columns)
            campaign.save()
            return JsonResponse({'status': 'success'})
        except Campaign.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Campaign not found'})
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

def send_qr_email(player, id , files):
    qr_image = generate_qr_code(str(player.registration_code))   
    qr_image.seek(0)  # Ensure pointer at start

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
    
    email = EmailMultiAlternatives(
        subject='Your Admission QR Code for ' + campaign.title,
        body=html_content,
        from_email=formataddr((campaign.title, settings.DEFAULT_FROM_EMAIL)),
        to=[player.email],
        headers = {"Reply-To": "info@pikom.org.my"}
    )
    email.attach_alternative(html_content, "text/html")

    # Attach banner image
    banner_path = os.path.join(settings.BASE_DIR, "register", "static", "register","email", f"banner_{id}.png")
    with open(banner_path, 'rb') as f:
        banner = MIMEImage(f.read())
        banner.add_header('Content-ID', '<banner>')
        banner.add_header('Content-Disposition', 'inline', filename=f"banner_{id}.png")
        email.attach(banner)

    # Attach another image
    # logo_path = os.path.join(settings.BASE_DIR, "register", "static", "register","email","agenda.png")
    # with open(logo_path, 'rb') as f:
    #     agenda = MIMEImage(f.read())
    #     agenda.add_header('Content-ID', '<agenda>')
    #     agenda.add_header('Content-Disposition', 'inline', filename="agenda.png")
    #     email.attach(agenda)

    # Create MIMEImage for QR
    qr_mime = MIMEImage(qr_image.read())
    qr_mime.add_header('Content-ID', '<qrcode>')
    qr_mime.add_header('Content-Disposition', 'inline', filename=f'qrcode_{player.name}.png')
    email.attach(qr_mime)

    #email.attach(f'qr_{player.name}.png', qr_image.read(), 'image/png')
    
    for f in files:
        email.attach(f.name, f.read(), f.content_type)

    
    # email = EmailMessage(
    #     subject='Your Admission QR Code for ' + campaign.title,
    #     body=html_content,
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     to=[player.email],
    # )
    # email.content_subtype = 'html'
    # email.attach(f'qr_{player.name}.png', qr_image.read(), 'image/png')
    # for f in files:
    #     email.attach(f.name, f.read(), f.content_type)
   
    try:
        email.send()
        player.qr_sent = True
        player.save()
        return True
    except Exception as e:     
        print(f"Error sending email to {player.email}: {str(e)}")   
        return False    

def send_qr(request, id):
    #get data from json
    #data = json.loads(request.body)
    #reg_no_list = data.get('ids', [])
    reg_no_list = request.POST["ids"] 
    files = request.FILES.getlist("files") 

    #convert json list in list
    reg_no_list = json.loads(reg_no_list)

    #check if total file size is lesser than 10MB
    total_size = sum(f.size for f in files) < 10 * 1024 * 1024
   
    if not total_size:
        return JsonResponse({'success': False, 'message': 'Total file size exceeds 10MB limit.'})

    #print(f"Sending QR codes for campaign ID: {id} to players: {reg_no_list}")

    total_sent = 0
    total_players = len(reg_no_list)

    if id == "0": # from golf event
        players = Player.objects.filter(qr_sent=False)       
    else:
        id = id.replace("-", "")
        players = Submission.objects.filter(reg_no__in=reg_no_list, qr_sent=False, campaign_code=id)        

    total_players = players.count()
    for player in players:
        print(f"Sending QR code to player: {player.name}, email: {player.email}")
        if send_qr_email(player, id, files):
           total_sent += 1
    
    # if id == "0":
    #     players = Player.objects.filter(qr_sent=False)
    # else:
    #     id = id.replace("-", "")
    #     players = Submission.objects.filter(qr_sent=False, campaign_code=id)

    # total_sent = 0
    # total_players = players.count()
    # for player in players:
    #     if send_qr_email(player, id):
    #         total_sent += 1
    return JsonResponse({'success': True, 'message': f"QR codes sent successfully to {total_sent} out of {total_players} registered participants."})

@csrf_exempt
def talentgap2025_form(request):
    return render(request, 'register/admission/talentgap2025.html')

@csrf_exempt
def lead2025_form(request):
    campaign = Campaign.objects.filter(entry_keyword='lead2025').first()

    if campaign is None or campaign.is_active == False:
        return render(request, 'register/admission/lead2025_closed.html')
    return render(request, 'register/admission/lead2025.html')

@csrf_exempt
def save_submission(request):
    if request.method == 'POST':
        print("Saving submission")
        try:
            data = json.loads(request.body)
            print(data)           

            keyword = data.get('keyword', '').strip()
            is_instant = data.get('is_instant', False)

            #if keyword is not int, convert to int and key word isnothing about instant
            if keyword.isdigit() and is_instant:
                keyword = int(keyword)

            #campaign = Campaign.objects.filter(entry_keyword__iexact=keyword, is_active=True).first()
            if is_instant:
                campaign = Campaign.objects.filter(id=keyword, is_active=True).first()
            else:
                campaign = Campaign.objects.filter(entry_keyword__iexact=keyword, is_active=True).first()

            if campaign is None or campaign.is_active == False:                
                return JsonResponse({'success': False, 'message': 'Registration is closed.', 'code':'1'})

                
            
            c_id = campaign.campaign_code if campaign else None            

            member = data.get('is_member')
            checkin = data.get('is_checkin')            

            category = data.get('category', '')
            promocode = data.get('promo_code', '')
            consent = data.get('consent', 'No')
           
            if member and member == 'Yes':
                is_member = True
            else:
                is_member = False

            if checkin and checkin == 'Yes':
                is_checkin = True
            else:
                is_checkin = False

            if consent and consent == 'Yes':
                consent_given = True
            else:
                consent_given = False
            

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
                fkcampaign=campaign,
                is_checked_in=is_checkin,
                category=category,
                promo_code=promocode,
                consent=consent_given,
            )

            #update registrationno
            reg.reg_no = f"REG{reg.id:06d}"                
            reg.save()

            
            try:
                #campaign_code = c_id

                #campaign = Campaign.objects.filter(campaign_code=campaign_code).first()
                if campaign and campaign.pic_email and is_instant == False:
                    
                    html_content = render_to_string('register/email/submission_notification.html', {'title': campaign.title, 'url': 'https://pikom.talxone.com/submission_list/' + c_id.replace("-", "") + '/'})
                    valid_emails = []
                    for email in campaign.pic_email.split(','):
                        email = email.strip()
                        try:
                            validate_email(email)
                            valid_emails.append(email)
                        except ValidationError:                            
                            pass
                                    
                    email = EmailMessage(
                        subject='New Registration for ' + campaign.title,
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

@csrf_exempt
def submission_thankyou(request, reg_no):

    submission = Submission.objects.get(reg_no=reg_no)

    html_content = render_to_string('register/email/email_submission_thankyou.html', {'title': submission.fkcampaign.title,'name':submission.name,'reg_no':reg_no})

    email = EmailMultiAlternatives(
        subject=f'Your registration is successful - {reg_no}',
        body=html_content,
        from_email=formataddr((submission.fkcampaign.title, settings.DEFAULT_FROM_EMAIL)),
        to=[submission.email],
        headers={"Reply-To": "info@pikom.org.my"}
    )
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
    except Exception as e:
        print(f"Error sending email to {submission.email}: {str(e)}")

    return render(request, 'register/submission_thankyou.html', {'reg_no': reg_no})

@csrf_exempt
def survey(request, survey_id):

    survey = get_object_or_404(Survey, survey_code=survey_id)

    return render(
        request,
        "register/survey.html",
        {"survey": survey},
    )

@csrf_exempt
def survey_detail(request, survey_id, user_id):    

    survey = get_object_or_404(Survey, survey_code=survey_id)
    role_categories = [
        "Software Development",
        "Data & AI",
        "Cloud & DevOps",
        "Cybersecurity",
        "UI/UX & Product",
        "IT Infrastructure",
    ]

    #user_id = 1 if request.user.is_authenticated else None

    return render(
        request,
        "register/survey_detail.html",
        {"survey": survey, "role_categories": role_categories, "user_id":user_id},
    )

@csrf_exempt
def survey_initial_submit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method != "POST":
        return redirect("survey", survey_id=survey.survey_code)
    
    # Create a new survey user entry
    survey_user = SurveyUser.objects.create(
        survey=survey,
        name=request.POST.get("name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        organization=request.POST.get("organization"),
    )

    return redirect("survey_detail", survey_id=survey.survey_code, user_id=survey_user.id)

@csrf_exempt
def survey_submit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method != "POST":
        return redirect("survey_detail", survey_id=survey.id)
    
    user_id = request.POST.get("user_id")
    survey_user = get_object_or_404(SurveyUser, pk=user_id, survey=survey)

    campaign = Campaign.objects.filter(campaign_code=survey.fkcampaign.campaign_code).first()

    # Iterate all questions and read values from POST
    for q in survey.questions.all():
        field = f"q_{q.id}"

        if q.question_type in (Question.TYPE_TEXT, Question.TYPE_TEXTAREA):
            val = request.POST.get(field, "").strip()
            if val:
                Answer.objects.create(
                    survey=survey, question=q, user=survey_user,
                    answer_text=val
                )

        elif q.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
            picked = request.POST.get(field, "")
            other = request.POST.get(f"{field}_other", "").strip() if q.allow_other else ""
            if picked:
                # picked is one of the provided options; if "Other", also save other text if present
                data = [picked]
                Answer.objects.create(
                    survey=survey, question=q, user=survey_user,
                    selected_options=data, answer_text=other if picked == "Other" and other else None
                )
            elif q.allow_other and other:
                # no radio chosen but "Other" text provided (e.g. user typed without ticking)
                Answer.objects.create(
                    survey=survey, question=q, user=survey_user,
                    selected_options=["Other"], answer_text=other
                )

        elif q.question_type == Question.TYPE_CHECKBOX:
            picked = request.POST.getlist(field)
            other = request.POST.get(f"{field}_other", "").strip() if q.allow_other else ""
            # enforce max_checks server-side if set
            if q.max_checks and len(picked) > q.max_checks:
                picked = picked[: q.max_checks]
            if picked or other:
                if other and "Other" not in picked:
                    picked.append("Other")
                Answer.objects.create(
                    survey=survey, question=q, user=survey_user,
                    selected_options=picked, answer_text=other if other else None
                )

        elif q.question_type == Question.TYPE_MATRIX_ROLES:
            # Collect the 6 rows as per UI
            # Each row has: role_example, openings, urgency, difficulty
            categories = [
                "Software Development",
                "Data & AI",
                "Cloud & DevOps",
                "Cybersecurity",
                "UI/UX & Product",
                "IT Infrastructure",
            ]
            rows = []
            for idx, cat in enumerate(categories, start=1):
                prefix = f"{field}_row{idx}_"
                rows.append({
                    "category": cat,
                    "role_example": request.POST.get(prefix + "role", "").strip(),
                    "openings": request.POST.get(prefix + "openings", "").strip(),
                    "urgency": request.POST.get(prefix + "urgency", "").strip(),
                    "difficulty": request.POST.get(prefix + "difficulty", "").strip(),
                })
            # Save as JSON in answer_text
            Answer.objects.create(
                survey=survey, question=q, user=survey_user,
                answer_text=json.dumps(rows, ensure_ascii=False)
            )

    # try:
        
    #     if campaign and campaign.pic_email:
    #         c_id = str(campaign.campaign_code)
            
    #         html_content = render_to_string('register/email/submission_notification.html', {'title': campaign.title, 'url': 'https://pikom.talxone.com/submission_list/' + c_id.replace("-", "") + '/'})
    #         valid_emails = []
    #         for email in campaign.pic_email.split(','):
    #             email = email.strip()
    #             try:
    #                 validate_email(email)
    #                 valid_emails.append(email)
    #             except ValidationError:                            
    #                 pass
                            
    #         email = EmailMessage(
    #             subject='New Registration for ' + campaign.title,
    #             body=html_content,
    #             from_email=settings.DEFAULT_FROM_EMAIL,
    #             to=valid_emails,
    #         )
    #         email.content_subtype = 'html'
    #         email.send()

    # except ValueError:
    #     pass

    return redirect("survey_thankyou", survey_id=survey.survey_code)

@csrf_exempt
def survey_thankyou(request, survey_id):
    return render(request, "register/survey_thankyou.html", {"survey_id": survey_id})

@login_required
def survey_list(request):    
    current_user = request.user    

    #get all active campaigns
    campaigns = Campaign.objects.filter(is_active=True).order_by('-start_date')
    campaign_list = [{"id": str(c.id), "title": c.title} for c in campaigns]
    
    users = User.objects.all()
    user_data = [{"id": user.id, "email": user.email, "name": user.get_full_name()} for user in users]

    if current_user.is_superuser:
        # Show all surveys
        surveys = Survey.objects.all()
    else:
        # get list of survey id that has user id in SurveyTeam model
        surveys = Survey.objects.filter(fkcampaign__campaign_teams__user=current_user).distinct()

    return render(request, 'register/survey_list.html', {'user': current_user, 'surveys': surveys, 'users': user_data, 'campaigns': campaign_list})

@login_required
def create_survey(request):

    print("Creating or updating survey")

    if request.method == 'POST':
        id = request.POST.get('id')
        title = request.POST.get('title')
        start_date = parse_datetime(request.POST.get('start_date'))
        end_date = parse_datetime(request.POST.get('end_date'))
        is_active = request.POST.get('is_active') == 'true'
        description = request.POST.get("description")
        campaign_id = request.POST.get('campaign_id')
        campaign = get_object_or_404(Campaign, id=campaign_id) if campaign_id else None
        

        if id:
            #print(f"Updating survey with ID: {id}")
            survey = get_object_or_404(Survey, id=id)
            survey.title = title
            survey.start_date = start_date
            survey.end_date = end_date
            survey.is_active = is_active
            survey.description = description
            survey.fkcampaign = campaign
            survey.save()
        else:
            #print("Creating a new survey")
            survey = Survey.objects.create(
                title=title,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                description=description,
                fkcampaign=campaign
            )       

        return JsonResponse({'success': True, 'id': survey.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_survey(request, id):
    #print(f"Fetching survey data for ID: {id}")
    survey = get_object_or_404(Survey, id=id)  
  
    data = {
        "title": survey.title,
        "start_date": survey.start_date.isoformat() if survey.start_date else "",
        "end_date": survey.end_date.isoformat() if survey.end_date else "",       
        "active": survey.is_active,
        "id": survey.id,        
        "description": survey.description,
        "campaign_id": str(survey.fkcampaign.id) if survey.fkcampaign else None,
    }
    return JsonResponse(data)


@login_required 
def survey_submission_list(request, id=None):
    #print("Fetching submission list")
    current_user = request.user    

    survey = Survey.objects.get(id=id)
    return render(request, 'register/survey_submission_list.html', {'user': current_user, 'survey': survey})

@login_required
def get_survey_submission_list(request):   
    try:
        if request.method == 'POST':
            id = request.POST.get('id')              
            submissions = SurveyUser.objects.filter(survey_id=id).order_by('-created_at')
          

            data = []
            for s in submissions:
                data.append({     
                    'id': s.id,                                 
                    'name': s.name,
                    'email': s.email,
                    'phone': s.phone,
                    'organization': s.organization,
                    'submitted_date': s.created_at.strftime('%Y-%m-%d %I:%M %p') if s.created_at else '',  
                    'survey_id': s.survey.id,                 
                })

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def survey_answer_view(request, survey_id, user_id):
    # Get survey and survey user
    survey = get_object_or_404(Survey, id=survey_id)
    survey_user = get_object_or_404(SurveyUser, id=user_id, survey=survey)

    # Get all answers for this survey and user
    answers = Answer.objects.filter(survey=survey, user=survey_user).select_related("question")

    # Organize answers by question.id
    answer_dict = {ans.question.id: ans for ans in answers}

    #remove html tags from question text in asnwer_dict
    for q_id, ans in answer_dict.items():
        ans.question.text = strip_tags(ans.question.text)    

    return render(
        request,
        "register/survey_answer_view.html",
        {
            "survey": survey,
            "survey_user": survey_user,
            "answers": answer_dict,
        },
    )

@login_required
def send_survey_reminder(request, id):
   
    reg_no_list = request.POST["ids"] 

    #convert json list in list
    reg_no_list = json.loads(reg_no_list)   

    total_sent = 0
    total_players = len(reg_no_list)

    if id == "0": # from golf event
        players = Player.objects.filter(qr_sent=False)       
    else:
        id = id.replace("-", "")
        players = Submission.objects.filter(reg_no__in=reg_no_list, campaign_code=id) 

    #remove from players if email exist in SurveyUser table for the survey with campaign_code
    # survey = Survey.objects.filter(fkcampaign__campaign_code=id).first()       
    # if survey:
    #     existing_emails = SurveyUser.objects.filter(survey=survey).values_list('email', flat=True)
    #     players = players.exclude(email__in=existing_emails)

    campaign = Campaign.objects.filter(campaign_code=id).first()
    if not campaign :
        return JsonResponse({'success': False, 'message': 'No valid campaign found.'})
    
    email_item = {}
    email_item['title'] = campaign.title
    email_item['date'] = ''   
    email_item['banner'] = 'banner_' + id + '.png'
    email_item['subject'] = 'Thank You for Driving Change at ' + campaign.title
    email_item['template'] = f'email_reminder_{id}.html'

    total_players = players.count()
    for player in players:
        print(f"Sending reminder to player: {player.name}, email: {player.email}")
        if send_reminder_email(player, id, files=[], name='survey', email_item=email_item):
           total_sent += 1
   
    return JsonResponse({'success': True, 'message': f"Reminder sent successfully to {total_sent} out of {total_players} registered participants."})


def send_reminder_email(player, id , files, name, email_item):    

    if id == "0":
        template_name = 'email_registration.html'
    else:
        template_name = email_item['template']
        # if name == 'event':
        #     template_name = f'email_event_reminder_{id}.html'
        # else:
        #     template_name = f'email_reminder_{id}.html'


    try:
        registration_uuid = uuid.UUID(id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})
    
    campaign = get_object_or_404(Campaign, campaign_code=registration_uuid)

    #get the survey for the campaign
    survey = Survey.objects.filter(fkcampaign=campaign).first()


    html_content = render_to_string(f'register/email/{template_name}', {'name': player.name, 'id': survey.survey_code if survey else None, 'campaign': campaign})

   
    if not player.email:
        return False
    
    email = EmailMultiAlternatives(
        #subject='Thank You for Driving Change at ' + campaign.title,
        subject=email_item['subject'],
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[player.email],
    )
    email.attach_alternative(html_content, "text/html")

    # Attach banner image
    banner_path = os.path.join(settings.BASE_DIR, "register", "static", "register","email", email_item['banner'])
    with open(banner_path, 'rb') as f:
        banner = MIMEImage(f.read())
        banner.add_header('Content-ID', '<banner>')
        banner.add_header('Content-Disposition', 'inline', filename=email_item['banner'])
        email.attach(banner)

    
    for f in files:
        email.attach(f.name, f.read(), f.content_type)
    
   
    try:
        email.send()       
        return True
    except Exception as e:     
        print(f"Error sending email to {player.email}: {str(e)}")   
        return False    

def manual_checkin(request):
    if request.method == 'POST':
        id = request.POST.get('id', '').strip()   
        try:
            submission = Submission.objects.get(id=id)
            if submission.is_checked_in:
                return JsonResponse({'success': False, 'message': 'This participant has already checked in.'})

            submission.is_checked_in = True
            submission.save()

            return JsonResponse({'success': True, 'message': f'Check-in successful for {submission.name}.'})
        except Submission.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No matching registration found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def send_event_reminder(request, id):
   
    reg_no_list = request.POST["ids"] 

    #convert json list in list
    reg_no_list = json.loads(reg_no_list)   

    total_sent = 0
    total_players = len(reg_no_list)

    if id == "0": # from golf event
        players = Player.objects.filter(qr_sent=False)       
    else:
        id = id.replace("-", "")
        players = Submission.objects.filter(reg_no__in=reg_no_list, campaign_code=id) 

    #remove from players if email exist in SurveyUser table for the survey with campaign_code
    # survey = Survey.objects.filter(fkcampaign__campaign_code=id).first()       
    # if survey:
    #     existing_emails = SurveyUser.objects.filter(survey=survey).values_list('email', flat=True)
    #     players = players.exclude(email__in=existing_emails)

    campaign = Campaign.objects.filter(campaign_code=id).first()
    if not campaign :
        return JsonResponse({'success': False, 'message': 'No valid campaign found.'})
    
    email_item = {}
    email_item['title'] = campaign.title
    email_item['date'] = ''
    email_item['venue'] = 'To be announced'
    email_item['address'] = 'To be announced'
    email_item['city'] = 'To be announced'
    email_item['postcode'] = 'To be announced'
    email_item['state'] = 'To be announced'
    email_item['country'] = 'To be announced'
    email_item['contact_phone'] = 'To be announced'
    email_item['contact_email'] = 'To be announced'
    email_item['banner'] = 'banner_' + id + '.png'
    email_item['subject'] = 'Reminder To Attend: ' + campaign.title + ' on 25 November 2025'
    email_item['template'] = f'email_event_reminder_{id}.html'

    total_players = players.count()
    for player in players:
        print(f"Sending reminder to player: {player.name}, email: {player.email}")
        if send_reminder_email(player, id, files=[], name='event', email_item=email_item):
           total_sent += 1
   
    return JsonResponse({'success': True, 'message': f"Reminder sent successfully to {total_sent} out of {total_players} registered participants."})


