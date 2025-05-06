import csv
import random
import string
import base64

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Participant, CheckIn
from django.utils import timezone
from django.core.cache import cache


# Dashboard Home
def dashboard(request):
    total_registered = Participant.objects.count()
    total_checked_in = CheckIn.objects.count()
    context = {
        'total_registered': total_registered,
        'total_checked_in': total_checked_in
    }
    return render(request, 'dashboard.html', context)


# Participant Registration Page
def register(request):
    error_message = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        walking_distance_km = request.POST.get('walking_distance_km')
        gender = request.POST.get('gender')
        working_professional = request.POST.get('working_professional')
        o9_employee = request.POST.get('o9_employee')
        employee_code = request.POST.get('employee_code')
        company_name = request.POST.get('company_name')
        captcha_text = request.POST.get('captcha_text')

        # Captcha Validation
        stored_captcha = cache.get('current_captcha')
        if not stored_captcha or captcha_text.strip().lower() != stored_captcha.lower():
            error_message = "Invalid Captcha. Please try again."
        else:
            unique_id = f"PART{Participant.objects.count() + 1:04d}"
            participant = Participant.objects.create(
                name=name,
                email=email,
                phone_number=phone_number,
                walking_distance_km=walking_distance_km,
                unique_id=unique_id,
                gender=gender,
                working_professional=working_professional,
                o9_employee=o9_employee,
                employee_code=employee_code,
                company_name=company_name
            )
            return redirect('registered_list')

    # Always create a new captcha for GET request or after failed POST
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    cache.set('current_captcha', captcha_text, timeout=300)  # Captcha valid for 5 minutes

    context = {'captcha_text': captcha_text, 'error_message': error_message}
    return render(request, 'register.html', context)


# Serve Captcha Image
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.http import HttpResponse


def captcha_image(request):
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    cache.set('current_captcha', captcha_text, timeout=300)

    # Create an image with captcha_text
    image = Image.new('RGB', (150, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('arial.ttf', 30)
    except:
        font = ImageFont.load_default()
    draw.text((20, 10), captcha_text, font=font, fill=(0, 0, 0))

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.read(), content_type='image/png')


# Registered List
def registered_list(request):
    # Get the search query from the URL
    search_query = request.GET.get('search', '')

    # Fetch all participants
    participants = Participant.objects.all()

    # Apply search filter if a query exists
    if search_query:
        participants = participants.filter(
            Q(unique_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(gender__icontains=search_query) |
            Q(employee_code__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Paginate the results (20 participants per page)
    paginator = Paginator(participants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the paginated participants and page object to the template
    return render(request, 'registered_list.html', {
        'participants': page_obj.object_list,
        'page_obj': page_obj,
        'request': request,  # Pass request to preserve search query in template
    })


# Check In List
def checkin_list(request):
    checkins = CheckIn.objects.select_related('participant').all()
    return render(request, 'checkin_list.html', {'checkins': checkins})


# Scan Now Page
def scan_now(request):
    return render(request, 'scan_now.html')


# Processing the QR Scan result
def process_scan(request):
    if request.method == 'POST':
        scanned_data = request.POST.get('scanned_data')
        try:
            # Decode the scanned data (base64 encoded)
            decoded = base64.b64decode(scanned_data).decode('utf-8')
            unique_id, phone_number = decoded.split(',')

            # Find the participant by unique_id and phone_number
            participant = Participant.objects.get(unique_id=unique_id, phone_number=phone_number)

            # Check if participant is already checked-in
            checkin, created = CheckIn.objects.get_or_create(participant=participant)

            if created:
                # Success: Participant checked in for the first time
                return JsonResponse({'status': 'success', 'message': 'Participant Successfully Registered'})
            else:
                # Already checked-in
                return JsonResponse({'status': 'already_checked_in', 'message': 'Participant already checked-in'})

        except Participant.DoesNotExist:
            # Participant not found in the registered list
            return JsonResponse({'status': 'error', 'message': 'Participant not found in registered list'})
        except Exception as e:
            # General error (e.g., decoding failure, invalid data format)
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Invalid request method
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})


# Certificate Entries View
def certificate_entries(request):
    checked_in_participants = Participant.objects.filter(checkin__isnull=False).distinct()
    return render(request, 'certificate_entries.html', {'participants': checked_in_participants})


# Reports View
def reports(request):
    participants = Participant.objects.prefetch_related('checkin_set').all()
    total_registered = participants.count()
    total_checked_in = sum(1 for p in participants if p.checkin_set.exists())
    total_not_checked_in = total_registered - total_checked_in

    # Attach a property for easier template use
    for p in participants:
        p.checkin = p.checkin_set.first()

    context = {
        'total_registered': total_registered,
        'total_checked_in': total_checked_in,
        'total_not_checked_in': total_not_checked_in,
        'participants': participants
    }
    return render(request, 'reports.html', context)


# Logs Triggered View
def logs_triggered(request):
    checkin_logs = CheckIn.objects.select_related('participant').order_by('-checkin_time')
    return render(request, 'logs_triggered.html', {'checkin_logs': checkin_logs})


def export_participants_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="participants_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Unique ID', 'Name', 'Email', 'Phone Number', 'Registered At', 'Checked In'])

    participants = Participant.objects.all()
    for participant in participants:
        checked_in = CheckIn.objects.filter(participant=participant).exists()
        writer.writerow([
            participant.unique_id,
            participant.name,
            participant.email,
            participant.phone_number,
            participant.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if checked_in else 'No'
        ])
    return response
