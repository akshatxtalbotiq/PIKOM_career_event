from email.utils import formataddr

from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.db.models import Prefetch, Max
from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse, JsonResponse
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.validators import validate_email, ValidationError
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.db.models import Q

from django.contrib.auth.models import User
from io import BytesIO

from urllib3 import request
from picom import settings
from .models import Registration, Player, Sponsorship,Campaign, Submission,CampaignTeam, Survey, Question, Answer, SurveyUser, default_identity_field_config, merge_identity_field_config

import re
import uuid
import json
import qrcode

from django.views.decorators.csrf import csrf_exempt

from email.mime.image import MIMEImage
import os
from weasyprint import HTML


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
    user_data = [{"id": user.id, "email": user.email, "name": (user.get_full_name() or user.username) + ((" (" + user.email + ")") if user.email else "")} for user in users]

    if current_user.is_superuser:
        # Show all campaigns
        campaigns = Campaign.objects.all()
    else:
        # get list of campign id that has user id in CampaignTeam model
        campaigns = Campaign.objects.filter(campaign_teams__user=current_user).distinct()

    # Attach the campaign's registration form (if any) so the template can
    # link directly to /form/<survey_code>/, the builder, the check-in
    # scanner, etc. — no more pasting entry_url by hand.
    campaigns = list(campaigns)
    for c in campaigns:
        c.registration_form = (
            c.surveys
             .filter(purpose=Survey.PURPOSE_REGISTRATION)
             .order_by('-created_at')
             .first()
        )

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
        prompt_checkin_info = request.POST.get('prompt_checkin_info') == 'true'
        # Event theme colour — only accept a well-formed hex; anything else
        # falls back to the default green.
        theme_color = (request.POST.get('theme_color') or '').strip()
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", theme_color):
            theme_color = Campaign.THEME_DEFAULT

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
            campaign.prompt_checkin_info = prompt_checkin_info
            campaign.theme_color = theme_color
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
                entry_keyword=entry_keyword,
                prompt_checkin_info=prompt_checkin_info,
                theme_color=theme_color,
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
    user_data = [{"id": user.id, "email": user.email, "name": (user.get_full_name() or user.username) + ((" (" + user.email + ")") if user.email else "")} for user in users] 

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
        "selected_users": selected_users,
        "enable_prompt": campaign.prompt_checkin_info,
        "theme_color": campaign.theme,
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
        headers = {"Reply-To": _reply_to_header(campaign)}
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

def remove_submissions(request):
    if request.method == 'POST':
        try:
            reg_no_list = request.POST["ids"]  
            campaign_id = request.POST["campaign_id"]          
            #convert json list in list
            reg_no_list = json.loads(reg_no_list)

            print(f"Removing submissions with registration numbers: {reg_no_list}")
            print(f"From campaign ID: {campaign_id}")
            deleted_count = Submission.objects.filter(reg_no__in=reg_no_list, fkcampaign__id = campaign_id).delete()
            # Delete submissions with the given registration numbers
            #deleted_count, _ = Submission.objects.filter(reg_no__in=reg_nos).delete()

            return JsonResponse({'success': True, 'message': f'Successfully deleted {deleted_count[0]} submissions.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


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
        headers={"Reply-To": _reply_to_header(submission.fkcampaign)}
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

def _surveys_for_user(request, purpose):
    """Surveys visible to the current user, filtered by purpose."""
    current_user = request.user
    if current_user.is_superuser:
        qs = Survey.objects.filter(purpose=purpose)
    else:
        qs = Survey.objects.filter(
            purpose=purpose,
            fkcampaign__campaign_teams__user=current_user,
        ).distinct()
    return qs.order_by('-created_at')


@login_required
def survey_list(request):
    current_user = request.user
    campaigns = Campaign.objects.filter(is_active=True).order_by('-start_date')
    campaign_list = [{"id": str(c.id), "title": c.title} for c in campaigns]

    users = User.objects.all()
    user_data = [{"id": user.id, "email": user.email, "name": (user.get_full_name() or user.username) + ((" (" + user.email + ")") if user.email else "")} for user in users]

    surveys = _surveys_for_user(request, Survey.PURPOSE_FEEDBACK)

    return render(request, 'register/survey_list.html', {
        'user': current_user,
        'surveys': surveys,
        'users': user_data,
        'campaigns': campaign_list,
        'list_purpose': Survey.PURPOSE_FEEDBACK,
        'list_title': 'Post-event Surveys',
        'list_subtitle': 'List of surveys sent to attendees after events',
        'new_button_label': 'New Survey',
        'modal_title': 'Add New Survey',
    })


@login_required
def registration_form_list(request):
    current_user = request.user
    campaigns = Campaign.objects.filter(is_active=True).order_by('-start_date')
    campaign_list = [{"id": str(c.id), "title": c.title} for c in campaigns]

    users = User.objects.all()
    user_data = [{"id": user.id, "email": user.email, "name": (user.get_full_name() or user.username) + ((" (" + user.email + ")") if user.email else "")} for user in users]

    surveys = _surveys_for_user(request, Survey.PURPOSE_REGISTRATION)

    # If the user clicked "Create form" from a Campaign row, we receive
    # ?for_campaign=<id> and auto-open the create modal with that campaign
    # pre-selected.
    auto_open_campaign_id = request.GET.get('for_campaign') or ''

    return render(request, 'register/survey_list.html', {
        'user': current_user,
        'surveys': surveys,
        'users': user_data,
        'campaigns': campaign_list,
        'list_purpose': Survey.PURPOSE_REGISTRATION,
        'list_title': 'Registration Forms',
        'list_subtitle': 'Forms that invitees fill in to register for an event',
        'new_button_label': 'New Registration Form',
        'modal_title': 'Add New Registration Form',
        'auto_open_campaign_id': auto_open_campaign_id,
    })

def _unique_slug(title, exclude_id=None):
    """Generate a unique Survey slug from `title`. Falls back to a numeric
    suffix if the base slug is taken."""
    base = slugify(title or "")[:70] or "form"
    slug = base
    n = 2
    qs = Survey.objects.all()
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    while qs.filter(slug=slug).exists():
        suffix = f"-{n}"
        slug = base[:70 - len(suffix)] + suffix
        n += 1
    return slug


@login_required
def clone_survey(request, survey_id):
    """Clone a form/survey together with all its questions, optionally
    assigning the copy to a different campaign. Submissions are NOT copied."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if not request.user.has_perm('register.add_survey'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    source = get_object_or_404(Survey, id=survey_id)

    title = (request.POST.get('title') or '').strip() or f"Copy of {source.title}"
    campaign_id = request.POST.get('campaign_id')
    campaign = get_object_or_404(Campaign, id=campaign_id) if campaign_id else None

    with transaction.atomic():
        clone = Survey.objects.create(
            title=title,
            slug=_unique_slug(title),
            description=source.description,
            fkcampaign=campaign,
            start_date=source.start_date,
            end_date=source.end_date,
            is_active=source.is_active,
            purpose=source.purpose,
            identity_field_config=source.identity_field_config,
        )

        # Copy the banner file (a real copy, so deleting one form's banner
        # never breaks the other).
        if source.banner:
            try:
                source.banner.open('rb')
                clone.banner.save(
                    os.path.basename(source.banner.name),
                    ContentFile(source.banner.read()),
                    save=True,
                )
            except FileNotFoundError:
                pass
            finally:
                source.banner.close()

        Question.objects.bulk_create([
            Question(
                survey=clone,
                number=q.number,
                text=q.text,
                help_text=q.help_text,
                question_type=q.question_type,
                show_in_list=q.show_in_list,
                list_column_label=q.list_column_label,
                choices=q.choices,
                allow_other=q.allow_other,
                max_checks=q.max_checks,
                is_required=q.is_required,
                choice_followups=q.choice_followups,
            )
            for q in source.questions.all()
        ])

    return JsonResponse({'success': True, 'id': clone.id})


@login_required
def delete_survey(request, survey_id):
    """Delete a form/survey. Cascades to its questions, submissions and answers."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    if not request.user.has_perm('register.delete_survey'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    survey = get_object_or_404(Survey, id=survey_id)
    survey.delete()
    return JsonResponse({'success': True})


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
        

        purpose = request.POST.get('purpose') or Survey.PURPOSE_REGISTRATION
        if purpose not in {c[0] for c in Survey.PURPOSE_CHOICES}:
            purpose = Survey.PURPOSE_REGISTRATION

        # Optional slug from the modal; if provided, validate uniqueness.
        # If blank, we auto-generate from the title.
        raw_slug = (request.POST.get('slug') or '').strip()

        if id:
            survey = get_object_or_404(Survey, id=id)
            survey.title = title
            survey.start_date = start_date
            survey.end_date = end_date
            survey.is_active = is_active
            survey.description = description
            survey.fkcampaign = campaign
            survey.purpose = purpose
            # Update slug only if user explicitly changed it or it's missing
            if raw_slug:
                new_slug = slugify(raw_slug)[:80]
                if new_slug and new_slug != survey.slug:
                    if Survey.objects.filter(slug=new_slug).exclude(id=survey.id).exists():
                        return JsonResponse(
                            {'success': False, 'error': f"URL '{new_slug}' is already used by another form."},
                            status=400,
                        )
                    survey.slug = new_slug
            elif not survey.slug:
                survey.slug = _unique_slug(title, exclude_id=survey.id)
            survey.save()
        else:
            # If the admin typed a custom slug, use it (validated); else derive.
            if raw_slug:
                slug = slugify(raw_slug)[:80] or _unique_slug(title)
                if Survey.objects.filter(slug=slug).exists():
                    return JsonResponse(
                        {'success': False, 'error': f"URL '{slug}' is already used by another form."},
                        status=400,
                    )
            else:
                slug = _unique_slug(title)
            survey = Survey.objects.create(
                title=title,
                slug=slug,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                description=description,
                fkcampaign=campaign,
                purpose=purpose,
            )
            # For a new registration form, seed the 4 default identity Question
            # rows so the form is immediately usable end-to-end.
            if purpose == Survey.PURPOSE_REGISTRATION:
                defaults = [
                    (Question.TYPE_IDENTITY_NAME,         "Name",         True),
                    (Question.TYPE_IDENTITY_EMAIL,        "Email",        True),
                    (Question.TYPE_IDENTITY_PHONE,        "Phone",        False),
                    (Question.TYPE_IDENTITY_ORGANIZATION, "Organization", False),
                ]
                for idx, (qtype, label, req) in enumerate(defaults, start=1):
                    Question.objects.create(
                        survey=survey,
                        number=idx,
                        text=label,
                        question_type=qtype,
                        is_required=req,
                    )

        return JsonResponse({'success': True, 'id': survey.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_survey(request, id):
    #print(f"Fetching survey data for ID: {id}")
    survey = get_object_or_404(Survey, id=id)  
  
    data = {
        "title": survey.title,
        "slug": survey.slug or "",
        "start_date": survey.start_date.isoformat() if survey.start_date else "",
        "end_date": survey.end_date.isoformat() if survey.end_date else "",
        "active": survey.is_active,
        "id": survey.id,
        "description": survey.description,
        "campaign_id": str(survey.fkcampaign.id) if survey.fkcampaign else None,
        "purpose": survey.purpose,
    }
    return JsonResponse(data)


@login_required
def survey_submission_list(request, id=None):
    current_user = request.user
    survey = get_object_or_404(Survey, id=id)
    feedback_survey = None
    if survey.fkcampaign:
        feedback_survey = (
            Survey.objects
                  .filter(fkcampaign=survey.fkcampaign, purpose=Survey.PURPOSE_FEEDBACK, is_active=True)
                  .order_by('-created_at')
                  .first()
        )
    return render(request, 'register/survey_submission_list.html', {
        'user': current_user,
        'survey': survey,
        'campaign': survey.fkcampaign,
        'feedback_survey': feedback_survey,
    })

@login_required
def get_survey_submission_list(request):
    try:
        if request.method == 'POST':
            survey_id = request.POST.get('id')
            survey = get_object_or_404(Survey, id=survey_id)

            # Identity columns to show. Respects the visibility/label settings
            # the form owner configured in the form builder, so the list
            # mirrors what's actually being collected on the form.
            ident_cfg = merge_identity_field_config(survey.identity_field_config)
            identity_cols = [
                {
                    'key': item['key'],
                    'title': (item.get('label') or item['key'].title()),
                }
                for item in ident_cfg
                if item.get('visible', True) and item.get('key') in {'name', 'email', 'phone', 'organization'}
            ]

            # Custom questions the admin chose to surface as list columns
            shown_questions = list(
                survey.questions
                      .filter(show_in_list=True)
                      .exclude(question_type__in=Question.IDENTITY_TYPES.keys())
                      .order_by('number')
            )
            shown_qids = [q.id for q in shown_questions]

            # Pre-fetch answers for those questions so we don't N+1
            answers_qs = Answer.objects.filter(
                survey=survey,
                question_id__in=shown_qids,
            ).select_related('question')
            # {(user_id, question_id) -> Answer}
            answers_by_user_q = {(a.user_id, a.question_id): a for a in answers_qs}

            submissions = SurveyUser.objects.filter(survey_id=survey_id).order_by('-created_at')

            def render_answer(ans):
                if ans is None:
                    return ''
                if ans.selected_options:
                    return ', '.join(str(o) for o in ans.selected_options)
                if ans.answer_text:
                    return ans.answer_text
                return ''

            def fu_key(qid, option_label):
                # Stable per-question per-option key for the follow-up column.
                # Option labels are user-controlled but only used as a dict key,
                # so the raw value is fine inside JSON; we just avoid '.' for
                # DataTable's nested-dot lookup.
                return f"q_{qid}__fu__{option_label}".replace('.', '_')

            data = []
            checked_in_count = 0
            qr_sent_count = 0
            approved_count = 0
            pending_count = 0
            rejected_count = 0
            for s in submissions:
                custom = {}
                for q in shown_questions:
                    ans = answers_by_user_q.get((s.id, q.id))
                    custom[f'q_{q.id}'] = render_answer(ans)
                    # Pre-seed every configured follow-up column with an empty
                    # string so each row exposes the same keys. Without this,
                    # rows that didn't trigger a particular follow-up would be
                    # missing the key entirely and DataTables warns:
                    #   "Requested unknown parameter 'q_X__fu__...'".
                    if q.choice_followups:
                        for option in q.choice_followups.keys():
                            custom[fu_key(q.id, option)] = ''
                    # If this question has follow-ups, pull each one into its
                    # own column. Follow-up answers are stored as a JSON dict
                    # in Answer.answer_text — {"option label": "user text"}.
                    if q.choice_followups and ans and ans.answer_text:
                        try:
                            fu_data = json.loads(ans.answer_text)
                        except (json.JSONDecodeError, TypeError):
                            fu_data = None
                        if isinstance(fu_data, dict):
                            for option, fu_text in fu_data.items():
                                if option in q.choice_followups:
                                    custom[fu_key(q.id, option)] = fu_text
                if s.is_checked_in:
                    checked_in_count += 1
                if s.qr_sent:
                    qr_sent_count += 1
                if s.approval_status == SurveyUser.STATUS_APPROVED:
                    approved_count += 1
                elif s.approval_status == SurveyUser.STATUS_REJECTED:
                    rejected_count += 1
                else:
                    pending_count += 1
                row = {
                    'id': s.id,
                    'reg_no': s.reg_no or '',
                    'name': s.name,
                    'email': s.email,
                    'phone': s.phone,
                    'organization': s.organization,
                    'is_checked_in': s.is_checked_in,
                    'qr_sent': s.qr_sent,
                    'approval_status': s.approval_status,
                    'approved_at': s.approved_at.strftime('%Y-%m-%d %I:%M %p') if s.approved_at else '',
                    'approved_by': (s.approved_by.get_full_name() or s.approved_by.username) if s.approved_by else '',
                    'submitted_date': s.created_at.strftime('%Y-%m-%d %I:%M %p') if s.created_at else '',
                    'survey_id': s.survey.id,
                }
                row.update(custom)
                data.append(row)

            columns_meta = []
            for q in shown_questions:
                main_title = (
                    q.list_column_label
                    or (q.text or '').strip()[:60]
                    or f'Q{q.number}'
                )
                columns_meta.append({'id': q.id, 'title': main_title, 'key': f'q_{q.id}'})
                # One extra column per configured follow-up, headed by the
                # placeholder text the admin set in the builder.
                if q.choice_followups:
                    for option, placeholder in q.choice_followups.items():
                        columns_meta.append({
                            'id': q.id,
                            'title': placeholder or option,
                            'key': fu_key(q.id, option),
                            'is_followup': True,
                        })

            return JsonResponse({
                'data': data,
                'identity_cols': identity_cols,
                'columns': columns_meta,
                'totals': {
                    'all': len(data),
                    'checked_in': checked_in_count,
                    'qr_sent': qr_sent_count,
                    'approved': approved_count,
                    'pending': pending_count,
                    'rejected': rejected_count,
                },
            })
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

    # Identity questions (Name/Email/Phone/Organization) are already displayed
    # in the Respondent Information card at the top, and their answers live on
    # the SurveyUser row — not in Answer. Filter them out of the lower section
    # so we don't repeat the same fields with "no answer" placeholders.
    extra_questions = list(
        survey.questions
              .exclude(question_type__in=Question.IDENTITY_TYPES.keys())
              .order_by("number")
    )

    # Section title and empty-state copy depend on what kind of form this is.
    if survey.purpose == Survey.PURPOSE_REGISTRATION:
        responses_section_title = "Registration Details"
        responses_empty_text = "No additional questions on this registration form."
    else:
        responses_section_title = "Survey Responses"
        responses_empty_text = "No questions on this survey."

    return render(
        request,
        "register/survey_answer_view.html",
        {
            "survey": survey,
            "survey_user": survey_user,
            "answers": answer_dict,
            "extra_questions": extra_questions,
            "responses_section_title": responses_section_title,
            "responses_empty_text": responses_empty_text,
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

            return JsonResponse({'success': True, 'message': f'Check-in successful for {submission.name}.','name': submission.name, 'organization': submission.organization})
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


# ---------------------------------------------------------------------------
# Generic form builder — lets event owners author their own registration forms
# ---------------------------------------------------------------------------

@login_required
def form_builder(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    if not request.user.is_superuser:
        team_member = CampaignTeam.objects.filter(
            campaign=survey.fkcampaign, user=request.user
        ).exists() if survey.fkcampaign else False
        if not team_member:
            return HttpResponse(status=403)

    questions = survey.questions.all().order_by("number")
    public_url = request.build_absolute_uri(
        f"/event/{survey.slug or survey.survey_code}/"
    )
    return render(request, "register/form_builder.html", {
        "user": request.user,
        "survey": survey,
        "questions": questions,
        "public_url": public_url,
        "question_types": Question.QUESTION_TYPES,
        "identity_field_config": merge_identity_field_config(survey.identity_field_config),
    })


@login_required
def upload_banner(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    banner = request.FILES.get("banner")
    if not banner:
        return JsonResponse({"success": False, "message": "No file uploaded"}, status=400)
    if banner.size > 5 * 1024 * 1024:
        return JsonResponse({"success": False, "message": "Banner must be under 5 MB"}, status=400)
    if not banner.content_type.startswith("image/"):
        return JsonResponse({"success": False, "message": "File must be an image"}, status=400)
    # Replace any existing banner
    if survey.banner:
        survey.banner.delete(save=False)
    survey.banner = banner
    survey.save(update_fields=["banner"])
    return JsonResponse({"success": True, "url": survey.banner.url})


@login_required
def delete_banner(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    if survey.banner:
        survey.banner.delete(save=False)
        survey.banner = None
        survey.save(update_fields=["banner"])
    return JsonResponse({"success": True})


@login_required
def save_identity_config(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    config = data.get("config")
    if not isinstance(config, list):
        return JsonResponse({"success": False, "message": "config must be a list"}, status=400)

    allowed_keys = {"name", "email", "phone", "organization"}
    cleaned = []
    seen = set()
    for item in config:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if key not in allowed_keys or key in seen:
            continue
        seen.add(key)
        cleaned.append({
            "key": key,
            "label": (item.get("label") or key.title()).strip()[:100],
            "visible": bool(item.get("visible", True)),
            "required": bool(item.get("required", False)),
        })
    # Force-include any missing keys so the config is always complete. Use each
    # field's default visibility (not a hard False) so a field that simply
    # wasn't in the posted payload — e.g. on an older form — isn't silently
    # hidden from the registrations list.
    defaults = {f["key"]: f for f in default_identity_field_config()}
    for k in ["name", "email", "phone", "organization"]:
        if k not in seen:
            cleaned.append(dict(defaults[k]))

    survey = get_object_or_404(Survey, id=survey_id)
    survey.identity_field_config = cleaned
    survey.save(update_fields=["identity_field_config"])
    return JsonResponse({"success": True, "config": cleaned})


def _can_edit_campaign(request, campaign):
    """Superusers, or members of the campaign's team, may edit it."""
    if request.user.is_superuser:
        return True
    if not campaign:
        return False
    return CampaignTeam.objects.filter(campaign=campaign, user=request.user).exists()


def _sanitize_intro(raw_html):
    """Sanitise admin-authored rich-text on save (bleach allowlist). Degrades to
    pass-through only if bleach is unavailable (logged at import)."""
    raw_html = (raw_html or "").strip()
    if not raw_html or bleach is None:
        return raw_html
    return bleach.clean(raw_html, **_bleach_clean_kwargs())


@login_required
def save_event_details(request, campaign_id):
    """Save campaign-level event facts shown in the QR/reminder emails."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if not _can_edit_campaign(request, campaign):
        return HttpResponse(status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    campaign.event_time = (data.get("event_time") or "").strip()[:120]
    campaign.venue = (data.get("venue") or "").strip()
    campaign.dress_code = (data.get("dress_code") or "").strip()[:120]

    cleaned = []
    rows = data.get("extra_info")
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            row = {
                "icon": (item.get("icon") or "").strip()[:8],
                "label": (item.get("label") or "").strip()[:120],
                "value": (item.get("value") or "").strip()[:500],
                "link": (item.get("link") or "").strip()[:500],
            }
            if row["label"] or row["value"] or row["link"]:
                cleaned.append(row)
    campaign.extra_info = cleaned

    campaign.save(update_fields=["event_time", "venue", "dress_code", "extra_info"])

    # Survey-level toggle: show the event details block on the public
    # registration form. Sent along with the campaign payload because both
    # are edited on the same builder card.
    survey_id = data.get("survey_id")
    if survey_id and "show_on_form" in data:
        Survey.objects.filter(id=survey_id, fkcampaign=campaign).update(
            show_event_details=bool(data.get("show_on_form"))
        )

    return JsonResponse({"success": True, "extra_info": cleaned})


@login_required
def save_email_content(request, campaign_id):
    """Save campaign-level email message text (sanitised rich-text) + sign-off."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if not _can_edit_campaign(request, campaign):
        return HttpResponse(status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    campaign.qr_email_intro = _sanitize_intro(data.get("qr_email_intro"))
    campaign.reminder_intro = _sanitize_intro(data.get("reminder_intro"))
    campaign.thankyou_intro = _sanitize_intro(data.get("thankyou_intro"))
    campaign.email_signoff = _sanitize_intro(data.get("email_signoff"))
    # Subjects are plain text; collapse whitespace to a single line.
    campaign.qr_email_subject = " ".join((data.get("qr_email_subject") or "").split())[:200]
    campaign.reminder_subject = " ".join((data.get("reminder_subject") or "").split())[:200]
    campaign.thankyou_subject = " ".join((data.get("thankyou_subject") or "").split())[:200]
    campaign.show_details_qr = bool(data.get("show_details_qr", True))
    campaign.show_details_reminder = bool(data.get("show_details_reminder", True))
    campaign.show_details_thankyou = bool(data.get("show_details_thankyou", False))
    campaign.save(update_fields=[
        "qr_email_intro", "reminder_intro", "thankyou_intro", "email_signoff",
        "qr_email_subject", "reminder_subject", "thankyou_subject",
        "show_details_qr", "show_details_reminder", "show_details_thankyou",
    ])
    return JsonResponse({
        "success": True,
        "qr_email_intro": campaign.qr_email_intro,
        "reminder_intro": campaign.reminder_intro,
    })


@login_required
def preview_email(request, survey_id, kind):
    """Render the QR or reminder email with sample registrant data so the
    form author can see the result. kind = 'qr' | 'reminder'."""
    import base64

    survey = get_object_or_404(Survey, id=survey_id)
    if not _can_edit_campaign(request, survey.fkcampaign) and not request.user.is_superuser:
        return HttpResponse(status=403)
    campaign = survey.fkcampaign
    base = _email_base_url(request)
    banner_url = (base + survey.banner.url) if survey.banner else ""
    event_date = campaign.end_date if campaign else None
    title = (campaign.title if campaign else survey.title) or ""
    tag_ctx = {
        "name": "Jane Tan",
        "reg_no": "REG-00123",
        "event_date": _date_filter(event_date, "j F Y") if event_date else "",
        "title": title,
    }
    intro_field = {
        "qr": "qr_email_intro",
        "reminder": "reminder_intro",
        "thankyou": "thankyou_intro",
    }.get(kind, "reminder_intro")
    detail_flag = {
        "qr": "show_details_qr",
        "reminder": "show_details_reminder",
        "thankyou": "show_details_thankyou",
    }.get(kind, "show_details_reminder")
    subject_field = {
        "qr": "qr_email_subject",
        "reminder": "reminder_subject",
        "thankyou": "thankyou_subject",
    }.get(kind, "reminder_subject")
    default_subject = {
        "qr": f"You're registered for {title} — your check-in QR code",
        "reminder": f"Reminder to Attend: {title}",
        "thankyou": f"Thank you for your registration — {title}",
    }.get(kind, f"Reminder to Attend: {title}")
    preview_subject = _render_subject(
        getattr(campaign, subject_field, "") if campaign else "", tag_ctx
    ) or default_subject
    ctx = dict(tag_ctx)
    ctx["event_date"] = event_date
    theme = campaign.theme if campaign else Campaign.THEME_DEFAULT
    ctx.update({
        "survey": survey,
        "campaign": campaign,
        "banner_url": banner_url,
        "signoff_html": _signoff_html(campaign, title, theme),
        "intro_html": _render_intro(getattr(campaign, intro_field, "") or "", tag_ctx, theme) if campaign else "",
        "show_details": getattr(campaign, detail_flag, True) if campaign else True,
    })
    buf = BytesIO()
    qrcode.make("PREVIEW-REG-00123").save(buf, format="PNG")
    ctx["qr_src"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    if kind == "qr":
        template = "register/email/email_registration_qr.html"
    elif kind == "thankyou":
        template = "register/email/email_registration_received.html"
    else:
        ctx["show_qr"] = True
        template = "register/email/email_event_reminder_generic.html"
    # Show the (rendered) subject line above the email body so authors can
    # check it together with the content.
    subject_bar = (
        '<div style="background:#fff3cd; border-bottom:1px solid #ffe69c; '
        'padding:10px 16px; font:600 14px/1.4 Arial, sans-serif; color:#664d03;">'
        f'Subject: {_html_escape(preview_subject)}</div>'
    )
    html = render_to_string(template, ctx, request=request)
    return HttpResponse(subject_bar + html)


@login_required
def save_question(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    qid = data.get("id")
    survey_id = data.get("survey_id")
    text = (data.get("text") or "").strip()
    help_text = (data.get("help_text") or "").strip()
    question_type = data.get("question_type") or Question.TYPE_TEXT
    is_required = bool(data.get("is_required", False))
    allow_other = bool(data.get("allow_other", False))
    max_checks = data.get("max_checks") or None
    choices = data.get("choices") or []
    raw_followups = data.get("choice_followups") or {}
    show_in_list = bool(data.get("show_in_list", False))
    list_column_label = (data.get("list_column_label") or "").strip()[:60]

    if not text:
        return JsonResponse({"success": False, "message": "Question text is required"}, status=400)

    valid_types = {choice[0] for choice in Question.QUESTION_TYPES}
    # matrix_roles is reserved for the legacy PIKOM survey; identity types
    # are only created automatically (when the survey is created) and via
    # the data-migration backfill — not via the builder modal.
    valid_types.discard(Question.TYPE_MATRIX_ROLES)
    is_identity = question_type in Question.IDENTITY_TYPES
    if not qid and is_identity:
        # New questions can't pick an identity type from the builder modal.
        return JsonResponse({"success": False, "message": "Invalid question type"}, status=400)
    if question_type not in valid_types:
        return JsonResponse({"success": False, "message": "Invalid question type"}, status=400)

    needs_choices = question_type in (
        Question.TYPE_RADIO, Question.TYPE_CHECKBOX, Question.TYPE_SELECT
    )
    if needs_choices:
        choices = [c.strip() for c in choices if isinstance(c, str) and c.strip()]
        if not choices:
            return JsonResponse(
                {"success": False, "message": "At least one choice is required"},
                status=400,
            )
        # Keep only follow-ups whose key actually matches one of the choices.
        choice_followups = {}
        if isinstance(raw_followups, dict):
            for label, placeholder in raw_followups.items():
                if label in choices and isinstance(placeholder, str):
                    choice_followups[label] = placeholder.strip()[:200] or "Please specify"
        choice_followups = choice_followups or None
    else:
        choices = None
        allow_other = False
        choice_followups = None

    if max_checks not in (None, ""):
        try:
            max_checks = int(max_checks)
            if max_checks <= 0:
                max_checks = None
        except (TypeError, ValueError):
            max_checks = None
    else:
        max_checks = None

    if qid:
        question = get_object_or_404(Question, id=qid)
        question.text = text
        question.help_text = help_text
        question.question_type = question_type
        question.is_required = is_required
        question.allow_other = allow_other
        question.max_checks = max_checks if question_type == Question.TYPE_CHECKBOX else None
        question.choices = choices
        question.choice_followups = choice_followups
        # Identity questions are always implicitly in the list (Name/Email columns)
        question.show_in_list = show_in_list and not is_identity
        question.list_column_label = list_column_label
        question.save()
    else:
        survey = get_object_or_404(Survey, id=survey_id)
        next_number = (survey.questions.aggregate(m=Max("number"))["m"] or 0) + 1
        question = Question.objects.create(
            survey=survey,
            number=next_number,
            text=text,
            help_text=help_text,
            question_type=question_type,
            is_required=is_required,
            allow_other=allow_other,
            max_checks=max_checks if question_type == Question.TYPE_CHECKBOX else None,
            choices=choices,
            choice_followups=choice_followups,
            show_in_list=show_in_list,
            list_column_label=list_column_label,
        )

    return JsonResponse({"success": True, "id": question.id, "number": question.number})


@login_required
def get_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    return JsonResponse({
        "id": question.id,
        "survey_id": question.survey_id,
        "number": question.number,
        "text": question.text,
        "help_text": question.help_text,
        "question_type": question.question_type,
        "is_required": question.is_required,
        "allow_other": question.allow_other,
        "max_checks": question.max_checks,
        "choices": question.choices or [],
        "choice_followups": question.choice_followups or {},
        "show_in_list": question.show_in_list,
        "list_column_label": question.list_column_label or "",
    })


@login_required
def delete_question(request, question_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    question = get_object_or_404(Question, id=question_id)
    if question.question_type in Question.IDENTITY_TYPES:
        return JsonResponse(
            {"success": False, "message": "Identity fields cannot be deleted. Mark them optional instead."},
            status=400,
        )
    survey = question.survey
    question.delete()
    # Renumber remaining questions so display order stays 1..N
    for idx, q in enumerate(survey.questions.order_by("number"), start=1):
        if q.number != idx:
            q.number = idx
            q.save(update_fields=["number"])
    return JsonResponse({"success": True})


@login_required
def reorder_questions(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    order = data.get("order") or []
    survey = get_object_or_404(Survey, id=survey_id)
    with transaction.atomic():
        for idx, qid in enumerate(order, start=1):
            Question.objects.filter(id=qid, survey=survey).update(number=idx)
    return JsonResponse({"success": True})


# ---------------------------------------------------------------------------
# Public generic form flow (kept separate from the legacy /survey/ flow that
# is hardcoded for the PIKOM Talent Gap survey)
# ---------------------------------------------------------------------------

def _resolve_survey_by_identifier(identifier):
    """Look up a Survey by slug first; fall back to the UUID survey_code so
    legacy links / QR codes keep working."""
    survey = Survey.objects.filter(slug=identifier).first()
    if survey:
        return survey
    try:
        return get_object_or_404(Survey, survey_code=identifier)
    except (ValueError, Survey.DoesNotExist):
        from django.http import Http404
        raise Http404("Form not found")


def form_public(request, survey_code):
    # `survey_code` is named for backwards compat with reverse() callers, but it
    # may be either a slug ("cio-conference-2026") or a UUID.
    survey = _resolve_survey_by_identifier(survey_code)
    return render(request, "register/form_public.html", {
        "survey": survey,
    })


@login_required
def form_preview(request, survey_id):
    """Owner-only preview. Renders the public form exactly as participants
    will see it, but flagged so the submit handler is a no-op (no DB writes)."""
    survey = get_object_or_404(Survey, id=survey_id)
    if not request.user.is_superuser:
        team_member = CampaignTeam.objects.filter(
            campaign=survey.fkcampaign, user=request.user
        ).exists() if survey.fkcampaign else False
        if not team_member:
            return HttpResponse(status=403)
    return render(request, "register/form_public.html", {
        "survey": survey,
        "preview_mode": True,
    })


@csrf_exempt
def form_initial_submit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method != "POST" or not survey.is_active:
        return redirect("form_public", survey_code=survey.survey_code)

    survey_user = SurveyUser.objects.create(
        survey=survey,
        name=(request.POST.get("name") or "").strip(),
        email=(request.POST.get("email") or "").strip(),
        phone=(request.POST.get("phone") or "").strip(),
        organization=(request.POST.get("organization") or "").strip(),
    )

    public_ident = survey.slug or str(survey.survey_code)
    if not survey.questions.exists():
        return redirect("form_thankyou", survey_code=public_ident, user_id=survey_user.id)
    return redirect("form_detail", survey_code=public_ident, user_id=survey_user.id)


def form_detail(request, survey_code, user_id):
    survey = _resolve_survey_by_identifier(survey_code)
    survey_user = get_object_or_404(SurveyUser, pk=user_id, survey=survey)
    return render(request, "register/form_detail.html", {
        "survey": survey,
        "survey_user": survey_user,
    })


@csrf_exempt
def form_submit(request, survey_id):
    """Single-page submission: creates SurveyUser from identity questions and
    Answer rows for everything else, in one transaction."""
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method != "POST":
        return redirect("form_public", survey_code=survey.survey_code)

    # Server-side enforcement of required questions. The browser uses
    # `novalidate`, and JS validation can be bypassed (curl, JS disabled),
    # so a blank-but-required field must be rejected here too.
    questions = list(survey.questions.all())
    missing = []
    for q in questions:
        if not q.is_required:
            continue
        field = f"q_{q.id}"
        if q.question_type == Question.TYPE_CHECKBOX:
            picked = request.POST.getlist(field)
            other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
            has_value = bool([p for p in picked if p.strip()]) or bool(other)
        elif q.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
            picked = (request.POST.get(field) or "").strip()
            other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
            has_value = bool(picked) or bool(other)
        else:
            has_value = bool((request.POST.get(field) or "").strip())
        if not has_value:
            label = strip_tags(q.text or "").strip()
            missing.append(label or f"Question {q.id}")

    if missing:
        messages.error(
            request,
            "Please complete all required fields: " + ", ".join(missing),
        )
        return redirect("form_public", survey_code=(survey.slug or str(survey.survey_code)))

    with transaction.atomic():
        # 1) Pull identity values out of POST so we can construct SurveyUser.
        identity_values = {}
        for q in questions:
            if q.question_type in Question.IDENTITY_TYPES:
                target_field = Question.IDENTITY_TYPES[q.question_type]
                identity_values[target_field] = (request.POST.get(f"q_{q.id}") or "").strip()

        survey_user = SurveyUser.objects.create(
            survey=survey,
            name=identity_values.get("name", ""),
            email=identity_values.get("email", ""),
            phone=identity_values.get("phone", ""),
            organization=identity_values.get("organization", ""),
        )
        # Assign a human-readable reference number now that the row has an id.
        survey_user.reg_no = f"REG{survey_user.id:06d}"
        survey_user.save(update_fields=["reg_no"])

        # 2) Save non-identity questions as Answer rows.
        for q in questions:
            if q.question_type in Question.IDENTITY_TYPES:
                continue
            field = f"q_{q.id}"

            if q.question_type in (Question.TYPE_TEXT, Question.TYPE_TEXTAREA):
                val = (request.POST.get(field) or "").strip()
                if val:
                    Answer.objects.create(
                        survey=survey, question=q, user=survey_user, answer_text=val
                    )

            elif q.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
                picked = request.POST.get(field, "")
                other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
                # Collect any configured follow-up text for the picked option
                followups = {}
                if picked and q.choice_followups and picked in q.choice_followups:
                    fu_val = (request.POST.get(f"{field}_followup_{picked}") or "").strip()
                    if fu_val:
                        followups[picked] = fu_val
                if picked:
                    answer_text = None
                    if picked == "Other" and other:
                        answer_text = other
                    elif followups:
                        answer_text = json.dumps(followups, ensure_ascii=False)
                    Answer.objects.create(
                        survey=survey, question=q, user=survey_user,
                        selected_options=[picked],
                        answer_text=answer_text,
                    )
                elif q.allow_other and other:
                    Answer.objects.create(
                        survey=survey, question=q, user=survey_user,
                        selected_options=["Other"], answer_text=other,
                    )

            elif q.question_type == Question.TYPE_CHECKBOX:
                picked = request.POST.getlist(field)
                other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
                if q.max_checks and len(picked) > q.max_checks:
                    picked = picked[: q.max_checks]
                # Follow-up text for each picked option that has one configured
                followups = {}
                if q.choice_followups:
                    for opt in picked:
                        if opt in q.choice_followups:
                            fu_val = (request.POST.get(f"{field}_followup_{opt}") or "").strip()
                            if fu_val:
                                followups[opt] = fu_val
                if picked or other:
                    if other and "Other" not in picked:
                        picked.append("Other")
                    if followups and not other:
                        answer_text = json.dumps(followups, ensure_ascii=False)
                    else:
                        answer_text = other if other else None
                    Answer.objects.create(
                        survey=survey, question=q, user=survey_user,
                        selected_options=picked,
                        answer_text=answer_text,
                    )

    # Send the "submission received — under review" email to the registrant
    # for registration-type forms (feedback surveys don't need it). Done
    # outside the atomic block so a mail backend hiccup can't roll back a
    # successful registration.
    if survey.purpose == Survey.PURPOSE_REGISTRATION:
        _send_registration_received_email(survey_user)

    return redirect("form_thankyou", survey_code=(survey.slug or str(survey.survey_code)), user_id=survey_user.id)


# ---------------------------------------------------------------------------
# Bulk actions on registrations (Send QR / reminders / Remove)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Shared email helpers: event details + sanitised rich-text intros.
# Used by the QR confirmation and attendance-reminder emails so event facts
# (date/time/venue/etc.) and message wording come from Campaign fields rather
# than being hardcoded in templates.
# ---------------------------------------------------------------------------
try:
    import bleach
except ImportError:  # bleach is a runtime dependency; degrade safely if absent.
    bleach = None

import re as _re
from django.utils.html import escape as _html_escape
from django.template.defaultfilters import date as _date_filter

_INTRO_ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "s", "ol", "ul", "li", "a", "span"]
_INTRO_ALLOWED_ATTRS = {"a": ["href"], "span": ["style"], "p": ["style"]}

# Allow font colour / highlight authored with the editor's colour pickers.
# bleach >= 5 needs an explicit CSS sanitizer (tinycss2) to keep style attrs;
# without it the style attribute is stripped, which is the safe degradation.
try:
    from bleach.css_sanitizer import CSSSanitizer
    _INTRO_CSS_SANITIZER = CSSSanitizer(allowed_css_properties=["color", "background-color"])
except Exception:
    _INTRO_CSS_SANITIZER = None


def _bleach_clean_kwargs():
    kwargs = dict(tags=_INTRO_ALLOWED_TAGS, attributes=_INTRO_ALLOWED_ATTRS, strip=True)
    if _INTRO_CSS_SANITIZER is not None:
        kwargs["css_sanitizer"] = _INTRO_CSS_SANITIZER
    return kwargs

# Friendly placeholders organisers insert, e.g. [Name], [Event], [Date],
# [Reg no]. These are plain find-and-replace tokens — NOT a template language —
# so authors never see or need to write any code syntax. Matching is
# case-insensitive and tolerant of inner spaces / underscores.
_PLACEHOLDER_RE = _re.compile(
    r"\[\s*(name|event|title|date|event[ _]date|reg[ _]?no)\s*\]", _re.IGNORECASE
)


def _email_base_url(request=None):
    """Absolute scheme+host for links/images in emails. Prefer the live request;
    fall back to the configured SITE_BASE_URL when none is available."""
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return (getattr(settings, "SITE_BASE_URL", "") or "").rstrip("/")


def _emailify_html(html, theme="#198754"):
    """Inline-style the few tags mail clients render inconsistently. Links are
    coloured with the campaign theme."""
    if not html:
        return ""
    html = html.replace("<a ", f'<a style="color:{theme};font-weight:600;" ')
    html = html.replace("<li>", '<li style="margin-bottom:6px;">')
    return html


def _signoff_html(campaign, title, theme="#198754"):
    """Email sign-off as HTML. Rich-text values authored in the builder render
    as-is (multi-line / bold / coloured, paragraphs tightened so rows read as
    consecutive lines). Legacy plain-text values and the blank fallback
    ("<Event> Team") render bolded, as before."""
    raw = ((campaign.email_signoff if campaign else "") or "").strip()
    if raw and "<" in raw:
        if strip_tags(raw).strip():
            return _emailify_html(raw, theme).replace("<p>", '<p style="margin:0;">')
        raw = ""  # empty editor markup, e.g. "<p><br></p>"
    return f"<strong>{_html_escape(raw or f'{title} Team')}</strong>"


def _render_intro(raw_html, tag_ctx, theme="#198754"):
    """Fill in friendly [Placeholders] with the recipient's details, then
    sanitise + emailify. Plain text substitution — no template engine — so
    organisers only ever deal with readable tokens like [Name]."""
    if not raw_html:
        return ""
    name = (tag_ctx.get("name") or "").strip() or "there"
    title = tag_ctx.get("title") or ""
    date = tag_ctx.get("event_date") or ""
    reg_no = tag_ctx.get("reg_no") or ""
    values = {
        "name": name,
        "event": title,
        "title": title,
        "date": date,
        "event date": date,
        "reg no": reg_no,
    }

    def _sub(m):
        key = m.group(1).lower().replace("_", " ")
        return _html_escape(values.get(key, m.group(0)))

    rendered = _PLACEHOLDER_RE.sub(_sub, raw_html)
    if bleach is not None:
        rendered = bleach.clean(rendered, **_bleach_clean_kwargs())
    return _emailify_html(rendered, theme)


def _reply_to_header(campaign):
    """Reply-To value for outgoing event emails: the campaign PIC email(s)
    when configured (comma-separated supported), else the PIKOM default.
    The actual sending account stays as configured in settings.py."""
    raw = (campaign.pic_email or "").strip() if campaign else ""
    addresses = [e.strip() for e in raw.split(",") if e.strip()]
    return ", ".join(addresses) if addresses else "info@pikom.org.my"


def _render_subject(raw, tag_ctx):
    """Fill in friendly [Placeholders] in a plain-text email subject.
    Same tokens as _render_intro but no HTML escaping/sanitising, and
    whitespace is collapsed (subjects must be a single line)."""
    if not raw:
        return ""
    name = (tag_ctx.get("name") or "").strip() or "there"
    title = tag_ctx.get("title") or ""
    date = tag_ctx.get("event_date") or ""
    reg_no = tag_ctx.get("reg_no") or ""
    values = {
        "name": name,
        "event": title,
        "title": title,
        "date": date,
        "event date": date,
        "reg no": reg_no,
    }

    def _sub(m):
        key = m.group(1).lower().replace("_", " ")
        return values.get(key, m.group(0))

    return " ".join(_PLACEHOLDER_RE.sub(_sub, raw).split())


def _event_email_ctx(survey_user, request=None, intro_field=None):
    """Build the shared context for event emails (QR, reminder). `intro_field`
    names the Campaign rich-text field to render into `intro_html`."""
    survey = survey_user.survey
    campaign = survey.fkcampaign if survey else None
    base = _email_base_url(request)
    banner_url = (base + survey.banner.url) if (survey and survey.banner) else ""
    event_date = campaign.end_date if campaign else None
    title = (campaign.title if campaign else (survey.title if survey else "")) or ""
    tag_ctx = {
        "name": survey_user.name or "",
        "reg_no": survey_user.reg_no or "",
        "event_date": _date_filter(event_date, "j F Y") if event_date else "",
        "title": title,
    }
    ctx = dict(tag_ctx)
    ctx["event_date"] = event_date  # datetime, for {{ event_date|date:... }} in templates
    ctx["event_date_str"] = tag_ctx["event_date"]  # formatted string, for subject merge tags
    detail_flag = {
        "qr_email_intro": "show_details_qr",
        "reminder_intro": "show_details_reminder",
        "thankyou_intro": "show_details_thankyou",
    }.get(intro_field)
    show_details = getattr(campaign, detail_flag, True) if (campaign and detail_flag) else True
    theme = campaign.theme if campaign else Campaign.THEME_DEFAULT
    signoff_html = _signoff_html(campaign, title, theme)
    ctx.update({
        "survey": survey,
        "campaign": campaign,
        "banner_url": banner_url,
        "signoff": strip_tags(signoff_html.replace("</p>", " </p>").replace("<br", " <br")).strip(),
        "signoff_html": signoff_html,
        "intro_html": _render_intro(getattr(campaign, intro_field, "") or "", tag_ctx, theme)
                      if (intro_field and campaign is not None) else "",
        "show_details": show_details,
    })
    return ctx


def _send_registration_received_email(survey_user):
    """Send the "thank you for your submission — under review" confirmation
    to the registrant immediately after they submit the form. Mirrors the
    on-screen thank-you page so the user has a record in their inbox.

    Best-effort: any error is logged but never raised, so a failed email
    can't break the registration submission itself.
    """
    if not survey_user or not survey_user.email:
        return False
    survey = survey_user.survey
    campaign = survey.fkcampaign if survey else None
    subject_title = (campaign.title if campaign else survey.title) or "your event"

    ctx = _event_email_ctx(survey_user, intro_field="thankyou_intro")
    # Subject: organiser-defined (with merge tags) falls back to the default.
    subject_tag_ctx = {
        "name": survey_user.name or "",
        "reg_no": survey_user.reg_no or "",
        "event_date": ctx.get("event_date_str") or "",
        "title": subject_title,
    }
    subject = _render_subject(
        campaign.thankyou_subject if campaign else "", subject_tag_ctx
    ) or f"Thank you for your registration — {subject_title}"
    try:
        html_content = render_to_string("register/email/email_registration_received.html", ctx)
        email = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html_content),
            from_email=formataddr((subject_title, settings.DEFAULT_FROM_EMAIL)),
            to=[survey_user.email],
            headers={"Reply-To": _reply_to_header(campaign)},
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True
    except Exception as e:
        # Never block the submission on email failure — log and move on.
        print(f"registration-received email failed for {survey_user.email}: {e}")
        return False


def _send_qr_to_surveyuser(survey_user, files=None, request=None):
    """Generate a QR image from the registration_code and email it. The QR is
    embedded inline (Content-ID: qrcode) so it renders inside the message body
    — the email template references it as <img src="cid:qrcode">. A regular
    attachment copy is also included so the recipient can save the PNG.
    Returns True on success.
    """
    if not survey_user.email:
        return False
    from io import BytesIO

    buf = BytesIO()
    qrcode.make(str(survey_user.registration_code)).save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    survey = survey_user.survey
    campaign = survey.fkcampaign

    ctx = _event_email_ctx(survey_user, request=request, intro_field="qr_email_intro")
    html_content = render_to_string("register/email/email_registration_qr.html", ctx)

    subject_title = ctx.get("title") or "your event"
    subject = _render_subject(
        (campaign.qr_email_subject if campaign else "") or "",
        {
            "name": ctx.get("name"),
            "reg_no": ctx.get("reg_no"),
            "event_date": ctx.get("event_date_str"),
            "title": subject_title,
        },
    ) or f"You're registered for {subject_title} — your check-in QR code"
    email = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_content),
        from_email=formataddr((subject_title, settings.DEFAULT_FROM_EMAIL)),
        to=[survey_user.email],
        headers={"Reply-To": _reply_to_header(campaign)},
    )
    # The HTML body needs to be a "related" alternative so the inline image
    # CID resolves. EmailMultiAlternatives + mixed/related is handled by
    # Django when we set mixed_subtype = 'related'. We also keep a regular
    # PNG attachment as a download so the recipient can save it.
    email.mixed_subtype = 'related'
    email.attach_alternative(html_content, "text/html")

    # Inline QR — referenced as <img src="cid:qrcode"> in the template.
    qr_inline = MIMEImage(qr_bytes, _subtype="png")
    qr_inline.add_header("Content-ID", "<qrcode>")
    qr_inline.add_header("Content-Disposition", "inline",
                         filename=f"qr_{survey_user.reg_no or survey_user.id}.png")
    email.attach(qr_inline)

    for f in (files or []):
        email.attach(f.name, f.read(), f.content_type)
    try:
        email.send()
        survey_user.qr_sent = True
        survey_user.save(update_fields=["qr_sent"])
        return True
    except Exception as e:
        print(f"send_qr error for {survey_user.email}: {e}")
        return False


@login_required
def send_survey_qr(request, survey_id):
    """POST: ids=[...] (optional), resend=0|1, files=[...].

    Single entry point for issuing QR-code emails. Behaviour:
      - If `ids` is non-empty, target that selection. Otherwise target every
        approved delegate (the "send to everyone we've vetted" mode).
      - Only delegates with approval_status=approved are ever emailed.
      - By default, delegates whose qr_sent is already True are skipped, so
        repeated clicks of "Send QR" don't spam people who already got it.
      - If `resend=1`, the qr_sent filter is dropped so an operator can
        resend to a participant who claims they didn't receive the email.
    The response itemises what was sent and what was skipped (why) so the
    operator gets clear feedback instead of a silent no-op.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)

    files = request.FILES.getlist("files")
    if sum(f.size for f in files) > 10 * 1024 * 1024:
        return JsonResponse({"success": False, "message": "Total attached files exceed 10 MB"}, status=400)

    resend = (request.POST.get("resend") or "").lower() in ("1", "true", "yes")

    try:
        ids = json.loads(request.POST.get("ids") or "[]")
    except json.JSONDecodeError:
        ids = []

    if ids:
        scope = SurveyUser.objects.filter(survey=survey, id__in=ids)
    else:
        scope = SurveyUser.objects.filter(survey=survey)

    approved = scope.filter(approval_status=SurveyUser.STATUS_APPROVED)
    skipped_pending = scope.filter(approval_status=SurveyUser.STATUS_PENDING).count() if ids else 0
    skipped_rejected = scope.filter(approval_status=SurveyUser.STATUS_REJECTED).count() if ids else 0

    if resend:
        recipients = approved
        skipped_already_sent = 0
    else:
        recipients = approved.filter(qr_sent=False)
        skipped_already_sent = approved.filter(qr_sent=True).count()

    target_count = recipients.count()
    sent = 0
    for u in recipients:
        if _send_qr_to_surveyuser(u, files, request=request):
            sent += 1

    skipped_bits = []
    if skipped_already_sent:
        skipped_bits.append(f"{skipped_already_sent} already received the QR (use Resend to override)")
    if skipped_pending:
        skipped_bits.append(f"{skipped_pending} pending review")
    if skipped_rejected:
        skipped_bits.append(f"{skipped_rejected} rejected")
    skipped_msg = f" Skipped: {'; '.join(skipped_bits)}." if skipped_bits else ""

    if target_count == 0:
        if skipped_bits:
            return JsonResponse({
                "success": False,
                "message": f"Nothing to send.{skipped_msg}",
            })
        return JsonResponse({
            "success": False,
            "message": "No approved delegates matched — approve some registrations first.",
        })

    verb = "Re-sent" if resend else "Sent"
    return JsonResponse({
        "success": True,
        "message": f"{verb} QR to {sent} of {target_count} approved delegate(s).{skipped_msg}",
    })


@login_required
def set_survey_user_status(request, survey_id):
    """POST: ids=[...], status=approved|rejected|pending. Bulk-set the vetting
    status for the selected registrations of this form."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    new_status = (request.POST.get("status") or "").strip().lower()
    valid = {SurveyUser.STATUS_APPROVED, SurveyUser.STATUS_REJECTED, SurveyUser.STATUS_PENDING}
    if new_status not in valid:
        return JsonResponse({"success": False, "message": "Invalid status."}, status=400)
    try:
        ids = json.loads(request.POST.get("ids") or "[]")
    except json.JSONDecodeError:
        ids = []
    if not ids:
        return JsonResponse({"success": False, "message": "No participants selected"}, status=400)

    qs = SurveyUser.objects.filter(survey=survey, id__in=ids)
    if new_status == SurveyUser.STATUS_APPROVED:
        qs.update(
            approval_status=new_status,
            approved_at=timezone.now(),
            approved_by=request.user,
        )
    elif new_status == SurveyUser.STATUS_REJECTED:
        qs.update(
            approval_status=new_status,
            approved_at=timezone.now(),
            approved_by=request.user,
        )
    else:
        qs.update(
            approval_status=new_status,
            approved_at=None,
            approved_by=None,
        )

    label = dict(SurveyUser.STATUS_CHOICES).get(new_status, new_status)
    return JsonResponse({
        "success": True,
        "message": f"{qs.count()} entr{'y' if qs.count() == 1 else 'ies'} marked {label}.",
    })


def _send_simple_email(survey_user, subject, template_name, extra_ctx=None, request=None, intro_field=None, subject_field=None, inline_qr=False):
    if not survey_user.email:
        return False
    ctx = _event_email_ctx(survey_user, request=request, intro_field=intro_field)
    if extra_ctx:
        ctx.update(extra_ctx)
    # Inline check-in QR (same CID mechanism as the registration-QR email).
    qr_bytes = None
    if inline_qr and survey_user.registration_code:
        from io import BytesIO
        buf = BytesIO()
        qrcode.make(str(survey_user.registration_code)).save(buf, format="PNG")
        qr_bytes = buf.getvalue()
        ctx["show_qr"] = True
    html_content = render_to_string(template_name, ctx)
    subject_title = ctx.get("title") or "your event"
    # A campaign-level custom subject (with [Event]/[Date]/... merge tags)
    # overrides the built-in default when present.
    campaign = survey_user.survey.fkcampaign if survey_user.survey else None
    custom_subject = getattr(campaign, subject_field, "") if (campaign and subject_field) else ""
    rendered_subject = _render_subject(custom_subject, {
        "name": ctx.get("name"),
        "reg_no": ctx.get("reg_no"),
        "event_date": ctx.get("event_date_str"),
        "title": subject_title,
    })
    email = EmailMultiAlternatives(
        subject=rendered_subject or subject.format(title=subject_title),
        body=html_content,
        from_email=formataddr((subject_title, settings.DEFAULT_FROM_EMAIL)),
        to=[survey_user.email],
        headers={"Reply-To": _reply_to_header(campaign)},
    )
    if qr_bytes:
        # The HTML body must be a "related" alternative so the cid:qrcode
        # reference resolves to the inline image.
        email.mixed_subtype = 'related'
    email.attach_alternative(html_content, "text/html")
    if qr_bytes:
        qr_inline = MIMEImage(qr_bytes, _subtype="png")
        qr_inline.add_header("Content-ID", "<qrcode>")
        qr_inline.add_header("Content-Disposition", "inline",
                             filename=f"qr_{survey_user.reg_no or survey_user.id}.png")
        email.attach(qr_inline)
    try:
        email.send()
        return True
    except Exception as e:
        print(f"email send error for {survey_user.email}: {e}")
        return False


@login_required
def send_survey_event_reminder(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    try:
        ids = json.loads(request.POST.get("ids") or "[]")
    except json.JSONDecodeError:
        ids = []
    if not ids:
        return JsonResponse({"success": False, "message": "No participants selected"}, status=400)
    selected = SurveyUser.objects.filter(survey=survey, id__in=ids)
    # Only approved participants get the reminder — mirrors the QR-send rule.
    approved = selected.filter(approval_status=SurveyUser.STATUS_APPROVED)
    skipped = selected.exclude(approval_status=SurveyUser.STATUS_APPROVED).count()
    if not approved.exists():
        return JsonResponse({
            "success": False,
            "message": "None of the selected participants are approved, so no reminders were sent.",
        }, status=400)
    sent = sum(
        1 for u in approved
        if _send_simple_email(
            u,
            "Reminder to Attend: {title}",
            "register/email/email_event_reminder_generic.html",
            request=request,
            intro_field="reminder_intro",
            subject_field="reminder_subject",
            inline_qr=True,
        )
    )
    msg = f"Event reminder sent to {sent} of {approved.count()} approved participant{'' if approved.count() == 1 else 's'}."
    if skipped:
        msg += f" Skipped {skipped} not yet approved."
    return JsonResponse({"success": True, "message": msg})


@login_required
def send_survey_feedback_reminder(request, survey_id):
    """Sends the post-event feedback-survey link to selected registrants of THIS
    registration form. Looks up the feedback Survey attached to the same campaign."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    if not survey.fkcampaign:
        return JsonResponse({"success": False, "message": "This form is not attached to a campaign."}, status=400)
    feedback = (
        Survey.objects
              .filter(fkcampaign=survey.fkcampaign, purpose=Survey.PURPOSE_FEEDBACK, is_active=True)
              .order_by('-created_at')
              .first()
    )
    if not feedback:
        return JsonResponse({"success": False, "message": "No active feedback survey set for this campaign."}, status=400)

    try:
        ids = json.loads(request.POST.get("ids") or "[]")
    except json.JSONDecodeError:
        ids = []
    if not ids:
        return JsonResponse({"success": False, "message": "No participants selected"}, status=400)

    survey_url = request.build_absolute_uri(f"/event/{feedback.slug or feedback.survey_code}/")
    users = SurveyUser.objects.filter(survey=survey, id__in=ids)
    sent = sum(
        1 for u in users
        if _send_simple_email(
            u,
            "Your feedback for {title}",
            "register/email/email_feedback_survey.html",
            extra_ctx={"survey_url": survey_url, "registration_survey": survey},
        )
    )
    return JsonResponse({"success": True, "message": f"Feedback survey link sent to {sent} of {users.count()}."})


@login_required
def delete_survey_users(request, survey_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    survey = get_object_or_404(Survey, id=survey_id)
    try:
        ids = json.loads(request.POST.get("ids") or "[]")
    except json.JSONDecodeError:
        ids = []
    if not ids:
        return JsonResponse({"success": False, "message": "No participants selected"}, status=400)
    deleted, _ = SurveyUser.objects.filter(survey=survey, id__in=ids).delete()
    return JsonResponse({"success": True, "message": f"{deleted} entr{'y' if deleted == 1 else 'ies'} removed."})


def form_thankyou(request, survey_code, user_id):
    survey = _resolve_survey_by_identifier(survey_code)
    survey_user = get_object_or_404(SurveyUser, pk=user_id, survey=survey)

    # Registration submissions are reviewed before a QR is issued. The QR is
    # only generated/emailed once the organiser approves the entry from the
    # dashboard, so the thank-you page no longer renders one inline.
    return render(request, "register/form_thankyou.html", {
        "survey": survey,
        "survey_user": survey_user,
        "is_registration": survey.purpose == Survey.PURPOSE_REGISTRATION,
    })


def build_answers_dict(submission):
    """
    Return {question_id: answer_obj} for one submission.
    Adjust this to your schema (SurveyAnswer etc.).
    """
    # Example if you have SurveyAnswer model with FK to submission and question:
    # answers = submission.answers.select_related("question").all()
    # return {a.question_id: a for a in answers}

    answers = submission.answers.all()  # adjust
    return {a.question_id: a for a in answers}

def survey_consolidated_pdf(request, survey_id):
    survey = get_object_or_404(
        Survey.objects.prefetch_related("questions"),
        survey_code=survey_id,
    )

    # Prefetch answers for each SurveyUser to avoid N+1 queries
    users_qs = (
        SurveyUser.objects
        .filter(survey=survey)
        .prefetch_related(
            Prefetch(
                "answer_set",  # default reverse name since Answer.user has no related_name
                queryset=Answer.objects.filter(survey=survey).select_related("question"),
            )
        )
        .order_by("-created_at")
    )

    submissions = []
    for u in users_qs:
        # Build {question_id: Answer}
        answers_dict = {a.question_id: a for a in u.answer_set.all()}
        submissions.append({
            "survey_user": u,
            "answers": answers_dict,
        })

    html_string = render_to_string(
        "register/consolidated_responses.html",  # your consolidated template
        {
            "survey": survey,
            "submissions": submissions,
        },
        request=request,
    )

    base_url = request.build_absolute_uri("/")  # helps WeasyPrint resolve relative assets

    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()

    filename = f"survey_{survey_id}_consolidated_responses.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

