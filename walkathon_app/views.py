import csv
import random
import string
import base64

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
import urllib.parse
import openpyxl
import pandas as pd
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Participant, CheckIn, CommunicationLog
from django.utils import timezone
from django.core.cache import cache
import uuid


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='CustomAdmin').exists())
def admin_dashboard(request):
    return render(request, 'dashboard.html')
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and (user.is_superuser or user.groups.filter(name='CustomAdmin').exists()):
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials or unauthorized user.'})
    return render(request, 'login.html')

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
            Participant.objects.create(
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
            messages.success(request, "Successfully Registered")
            return redirect('register')  # redirect back to the same registration page

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
    search_query = request.GET.get('search', '')
    source_filter = request.GET.get('source')
    participants = Participant.objects.all()
    if source_filter == 'form':
        participants = participants.filter(unique_id__startswith='PART')

    if search_query:
        participants = participants.filter(name__icontains=search_query)

    paginator = Paginator(participants, 15)  # 15 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'participants': participants,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'registered_list.html', context)


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
    search_query = request.GET.get('search', '')
    participants = Participant.objects.prefetch_related('checkin_set').all()
    total_registered = participants.count()
    total_checked_in = sum(1 for p in participants if p.checkin_set.exists())
    total_not_checked_in = total_registered - total_checked_in

    if search_query:
        participants = participants.filter(name__icontains=search_query)
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
def communication_logs(request):
    logs = CommunicationLog.objects.all().order_by('-created_on')  # Order by created_on for recent logs first
    return render(request, 'logs_triggered.html', {'checkin_logs': logs})


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


def upload_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        added_count = 0
        skipped_count = 0

        # Expecting headers: name | email | phone_number | walking_distance
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name, email, phone_number, walking_distance = row

            if not Participant.objects.filter(email=email, phone_number=phone_number).exists():
                Participant.objects.create(
                    unique_id=str(uuid.uuid4())[:8],
                    name=name,
                    email=email,
                    phone_number=phone_number,
                    walking_distance_km=walking_distance
                )
                added_count += 1
            else:
                skipped_count += 1

        print(f"Upload complete. Added: {added_count}, Skipped (duplicates): {skipped_count}")
        return redirect('upload_excel')

    # Pagination and optional search
    search_query = request.GET.get('search', '')
    participants = Participant.objects.all()

    if search_query:
        participants = participants.filter(Q(name__icontains=search_query))

    participants = participants.order_by('name')  # Add ordering to avoid pagination warning
    paginator = Paginator(participants, 15)  # 15 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query
    }
    return render(request, 'registered_list.html', context)


def bulk_ticket(request):
    if request.method == 'POST':
        message_text = "active"
        participants = Participant.objects.all()

        for p in participants:
            if p.email:
                send_mail(
                    subject="Walkathon Ticket",
                    message="Your walkathon ticket is now active.",
                    from_email=None,  # uses DEFAULT_FROM_EMAIL
                    recipient_list=[p.email],  # ✅ correct variable
                    fail_silently=False,
                )

            # WhatsApp Sending (Mock URL or actual API)
           # if p.phone_number:
                #phone_number = p.phone_number
                #encoded_message = urllib.parse.quote(f'Hello {p.name}, your ticket status: {message_text}')
                # Replace this URL with your WhatsApp API endpoint
                # Example using mock API or Twilio
               # whatsapp_api_url = f"https://api.whatsapp.com/send?phone={phone_number}&text={encoded_message}"

                # Uncomment below if using a real WhatsApp API with auth
                # response = requests.get(whatsapp_api_url, headers={'Authorization': 'Bearer YOUR_API_KEY'})

               # print(f"WhatsApp message to {phone_number}: {encoded_message}")  # Log/debug

        messages.success(request, "Bulk message sent to all registered participants.")
        return redirect('bulk_ticket')

    return render(request, 'bulk_ticket.html')