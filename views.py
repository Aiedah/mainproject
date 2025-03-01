from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.forms import modelformset_factory
from django.contrib import messages
from requests import request

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required
from .models import *


# Create your views here.
def home(request):
    return render(request, 'visitorsapps/home.html')
def adminpanel(request):
    return render(request, 'visitorsapps/adminpanel.html')
def resident_panel(request):
    return render(request, 'visitorsapps/resident_panel.html')
def resident_management(request):
    return render(request, 'visitorsapps/resident_management.html')


def view_flat(request):
    flats = FlatTab.objects.all()  # Fetch all flats
    context = {'flats': flats}
    return render(request, 'visitorsapps/view_flat.html', context)


def view_residents(request):
    residents = ResidentTab.objects.all()  # Fetch all residents
    context = {'residents': residents}
    return render(request, 'visitorsapps/view_residents.html', context)
from django.shortcuts import get_object_or_404, redirect
from .models import ResidentTab

def resident_delete(request, resident_id):
    # Get the resident object using the provided resident ID
    resident = get_object_or_404(ResidentTab, r_id=resident_id)

    if request.method == "POST":
        # Mark the resident as inactive
        resident.r_status = 'inactive'
        resident.save()

        # Also mark the linked user as inactive
        if resident.u_id:
            resident.u_id.is_active = False  # Deactivate the user
            resident.u_id.save()

            # Update the u_status in UserTab
            user_tab = UserTab.objects.filter(user=resident.u_id).first()
            if user_tab:
                user_tab.u_status = "inactive"
                user_tab.save()

        # Check if the resident's flat has no more active residents
        flat = resident.f_id  
        if flat and not ResidentTab.objects.filter(f_id=flat, r_status='active').exists():
            flat.occupied = False  # Mark flat as unoccupied
            flat.save()

    return redirect("view_residents")  # Redirect to the resident list page


from django.shortcuts import render, redirect
from .forms import *





from django.contrib import messages
from django.contrib.messages import get_messages

def add_vehicles(request):
    # Clear previous messages
    storage = get_messages(request)
    for _ in storage:
        pass  # This clears out any old messages

    # Get the logged-in user's resident record
    resident = ResidentTab.objects.filter(u_id=request.user).first()
    if not resident:
        messages.error(request, "Resident record not found.")
        return redirect("vehicle_details")

    existing_vehicle = VehicleTab.objects.filter(resident=resident).first()
    parking_slot = existing_vehicle.parking_slot if existing_vehicle else "Not Assigned"

    if request.method == "POST":
        form = VehicleForm(request.POST, resident=resident)
        if form.is_valid():
            vehicle_number = form.cleaned_data.get("vehicle_number")

            # Check if the vehicle already exists
            if VehicleTab.objects.filter(vehicle_number=vehicle_number, resident=resident).exists():
                messages.error(request, "Vehicle details already exist!")  # This should now be displayed
            else:
                vehicle = form.save(commit=False)
                vehicle.parking_slot = parking_slot
                vehicle.save()
                messages.success(request, "Vehicle added successfully!")
                return redirect("vehicle_details")  # Redirect ensures messages appear on new request

    else:
        form = VehicleForm(resident=resident)

    return render(request, "visitorsapps/add_vehicles.html", {"form": form, "parking_slot": parking_slot})







import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render

def generate_qr_code(request):
    visitor_form_url = request.build_absolute_uri('http://192.168.1.14:8000/visitor_entry/')  # Update with correct form URL

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(visitor_form_url)
    qr.make(fit=True)

    # Create QR Code Image
    img = qr.make_image(fill="black", back_color="white")

    # Convert Image to Bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    # Return QR Code as HTTP Response
    return HttpResponse(buffer.getvalue(), content_type="image/png")

def visitorscan(request):
    return render(request, 'visitorsapps/visitorscan.html')  # HTML template to display QR code







from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import LoginForm
from .models import UserTab

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            
            # Fetch user role
            user_tab = UserTab.objects.get(user=user)
            role = user_tab.userrole

            # Redirect based on role
            if role == "admin":
                return redirect("adminpanel")  # Change to your admin dashboard URL
            elif role == "resident":
                return redirect("resident_panel")  # Change to your resident dashboard URL
            else:
                messages.error(request, "Invalid role assigned.")
                return redirect("user_login")

        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = LoginForm()

    return render(request, "visitorsapps/user_login.html", {"form": form})

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("user_login")  # Redirect to login page







def resident_panel(request):
    resident = ResidentTab.objects.get(u_id=request.user)  # Fetch resident linked to logged-in user
    vehicle = VehicleTab.objects.filter(resident=resident).first()
    return render(request, 'visitorsapps/resident_panel.html', {'resident': resident})



def vehicle_details(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        try:
            # Get the resident linked to the current user (assuming you have a user-resident relationship)
            resident = request.user.residents.first()

            # Get all vehicles related to the current resident
            vehicles = VehicleTab.objects.filter(resident=resident)

            return render(request, 'visitorsapps/vehicle_details.html', {'vehicles': vehicles})

        except ResidentTab.DoesNotExist:
            # Handle the case where the user does not have an associated resident entry
            return render(request, 'visitorsapps/vehicle_details.html', {'error': 'No resident record found for this user.'})

    else:
        return redirect('user_login')  # Redirect to login if the user is not authenticated

from django.shortcuts import render, redirect
from django.utils.timezone import now
from .forms import VisitorForm

def visitor_entry(request):
    if request.method == "POST":
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)  # Do not save yet
            visitor.entry_time = now()  # Auto-set entry time
            visitor.save()  # Save visitor record
            return redirect('visitor_list')  # Redirect to visitor list after saving
    else:
        form = VisitorForm()

    return render(request, 'visitorsapps/visitor_entry.html', {'form': form})






def resident_details(request, resident_id):
    # Fetch the resident details
    resident = get_object_or_404(ResidentTab, r_id=resident_id)

    # Get the user's details from UserTab
    user_details = UserTab.objects.get(user=resident.u_id)

    # Fetch flat details
    flat_details = resident.f_id

    # Fetch vehicle details for the resident
    vehicle_details = VehicleTab.objects.filter(resident=resident)

    # Fetch ID proof details for the resident
    id_proofs = IDProof.objects.filter(resident=resident)

    # Pass all details to the template
    context = {
        'resident': resident,
        'user_details': user_details,
        'flat_details': flat_details,
        'vehicle_details': vehicle_details,
        'id_proofs': id_proofs,  # Add ID proof details to context
    }

    return render(request, 'visitorsapps/resident_details.html', context)
from django.shortcuts import render, redirect
from .forms import FlatForm

def add_flat(request):
    if request.method == "POST":
        form = FlatForm(request.POST)
        if form.is_valid():
            form.save()  # Save flat to database
            return redirect('view_flat')  # Redirect to flat list after saving
    else:
        form = FlatForm()

    return render(request, 'visitorsapps/add_flat.html', {'form': form})
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ResidentForm

def add_resident2(request):
    if request.method == 'POST':
        form = ResidentForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Resident added successfully!")
            return redirect('resident_management')  # Redirect to resident list page
        else:
            for error in form.errors.values():  # Show all validation errors
                messages.error(request, error)
    else:
        form = ResidentForm()
    
    return render(request, 'visitorsapps/add_resident2.html', {'form': form})





