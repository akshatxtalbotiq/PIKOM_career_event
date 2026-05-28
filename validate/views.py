from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from register.models import Player, Submission, Campaign, Survey, SurveyUser
import uuid

@login_required
def scan_page(request, id):
    id = id.strip()
    id = id.replace("-", "")
    try:
        registration_uuid = uuid.UUID(id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})

    campaign = Campaign.objects.filter(campaign_code=registration_uuid).first()

    return render(request, 'validate/scan.html', {
        'name': campaign.title,
        'validate_endpoint': '/validate/',
    })

@login_required
def scan_page_golf(request):
    return render(request, 'validate/scangolf.html')

@login_required
def scan_page_survey(request, survey_code):
    survey = get_object_or_404(Survey, survey_code=survey_code)
    return render(request, 'validate/scan.html', {
        'name': survey.title,
        'validate_endpoint': '/validatesurvey/',
    })

def validate(request, code):
    try:
        participant = Submission.objects.get(registration_code=code)

        if participant is None:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'})


        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'typ': 'new', 'name': participant.name, 'organization': participant.organization,'prompt_checkin_info': '1' if participant.fkcampaign.prompt_checkin_info else '0', 'message': '{0} checked in successfully!'.format(participant.name), 'remarks': participant.remarks},status=200)
        else:
            return JsonResponse({'typ': 'exist', 'name': participant.name, 'organization': participant.organization,'prompt_checkin_info': '1' if participant.fkcampaign.prompt_checkin_info else '0', 'message': '{0} already checked in!'.format(participant.name), 'remarks': participant.remarks},status=200)
    except Submission.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'},status=400)
    
def validategolf(request,code):
    try:
        participant = Player.objects.get(registration_code=code)

        if participant is None:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'})


        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'message': '{0} checked in successfully!'.format(participant.name), 'remarks': participant.remarks})
        else:
            return JsonResponse({'message': '{0} checked in successfully!'.format(participant.name), 'remarks': participant.remarks})
    except Player.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'})

def validatesurvey(request, code):
    try:
        participant = SurveyUser.objects.get(registration_code=code)
    except SurveyUser.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'}, status=400)

    # Gate check-in on approval. A pending or rejected delegate shouldn't have
    # received a QR in the first place, but defend in depth in case one slips
    # through (e.g. screenshot of someone else's pre-approval thank-you page).
    if participant.approval_status != getattr(participant, 'STATUS_APPROVED', 'approved'):
        return JsonResponse({
            'typ': 'blocked',
            'status': participant.approval_status,
            'name': participant.name or '',
            'organization': participant.organization or '',
            'reg_no': participant.reg_no or '',
            'message': 'Not approved for check-in (status: {0}).'.format(participant.approval_status),
        }, status=200)

    was_new = not participant.is_checked_in
    if was_new:
        participant.is_checked_in = True
        participant.save(update_fields=['is_checked_in'])

    return JsonResponse({
        'typ': 'new' if was_new else 'exist',
        'status': participant.approval_status,
        'name': participant.name or '',
        'organization': participant.organization or '',
        'reg_no': participant.reg_no or '',
        'message': '{0} checked in successfully!'.format(participant.name or 'Participant')
                   if was_new else
                   '{0} already checked in.'.format(participant.name or 'Participant'),
        'remarks': participant.remarks or '',
    }, status=200)