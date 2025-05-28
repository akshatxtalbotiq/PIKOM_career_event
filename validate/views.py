from django.shortcuts import render
from django.http import JsonResponse

from register.models import Player

def scan_page(request):
    return render(request, 'scan.html')

def validate(request, code):
    try:
        participant = Player.objects.get(registration_code=code)
        if not participant.is_checked_in:
            participant.is_checked_in = True
            participant.save()
            return JsonResponse({'message': f'{participant.name} checked in successfully!'})
        else:
            return JsonResponse({'message': f'{participant.name} already checked in!'})
    except Player.DoesNotExist:
        return JsonResponse({'message': 'Invalid QR code.'})