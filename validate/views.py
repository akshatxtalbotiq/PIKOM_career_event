from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse

from register.models import Player, Submission, Campaign
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

    return render(request, 'validate/scan.html', {'name': campaign.title})

@login_required
def scan_page_golf(request):
    return render(request, 'validate/scangolf.html')

def validate(request, code):
    try:
        participant = Submission.objects.get(registration_code=code)

        if participant is None:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'})


        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'message': '{0} checked in successfully!'.format(participant.name), 'remarks': participant.remarks},status=200)
        else:
            return JsonResponse({'message': '{0} checked in successfully!'.format(participant.name), 'remarks': participant.remarks},status=200)
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