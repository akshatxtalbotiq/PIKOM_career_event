from django.shortcuts import render
from django.http import JsonResponse

from register.models import Player, Submission, Campaign
import uuid

def scan_page(request, id):
    id = id.strip()
    id = id.replace("-", "")
    try:
        registration_uuid = uuid.UUID(id)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})
    
    campaign = Campaign.objects.filter(campaign_code=registration_uuid).first()

    return render(request, 'validate/scan.html', {'name': campaign.title})

def scan_page_golf(request):
    return render(request, 'validate/scangolf.html')

def validate(request, code):
    try:
        code = code.strip()
        code = code.replace("-", "")

        try:           
            registration_uuid = uuid.UUID(id)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})

        participant = Submission.objects.get(registration_code=registration_uuid)

        if participant is None:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'})


        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'message': f'Participant checked in successfully!', 'participant': participant})
        else:
            return JsonResponse({'message': f'Participant already checked in!', 'participant': participant})
    except Player.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'})
    
def validategolf(request,code):
    try:
        code = code.strip()
        code = code.replace("-", "")

        try:           
            registration_uuid = uuid.UUID(id)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid UUID format'})

        participant = Player.objects.get(registration_code=registration_uuid)        

        if participant is None:
            return JsonResponse({'status': 'error', 'message': 'Participant not found'})


        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'message': f'Participant checked in successfully!', 'participant': participant})
        else:
            return JsonResponse({'message': f'Participant already checked in!', 'participant': participant})
    except Player.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'})