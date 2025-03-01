from django.db import models
import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class UserTab(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    userrole = models.CharField(max_length=50, choices=[
      # ('visitor', 'Visitor'),
        ('resident', 'Resident'),
        ('admin', 'Admin'),
    ])
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    u_status = models.CharField(max_length=50,default="active")

    def __str__(self):
        return f"{self.user.username} - {self.userrole}"



class FlatTab(models.Model):
    """
    Represents a flat within a specific block and wing combination.
    """
    f_id = models.BigAutoField(primary_key=True)
    block_name = models.CharField(
        max_length=50,
        choices=[
            ('Block A', 'Block A'),
            ('Block B', 'Block B'),
        ]
    )
    wing_name = models.CharField(
        max_length=50,
        choices=[
            ('Wing A', 'Wing A'),
            ('Wing B', 'Wing B'),
        ]
    )
    floor = models.PositiveIntegerField()
    flat_number = models.CharField(max_length=20)
    size = models.CharField(
        max_length=10,
        choices=[
            ('2BHK', '2BHK'),
            ('3BHK', '3BHK'),
        ]
    )
    occupied =  models.BooleanField(default=False)
       

    class Meta:
        unique_together = (('flat_number', 'block_name', 'wing_name'),)  # Correct tuple format for unique_together

    def __str__(self):
        return f"Flat {self.flat_number} ({self.block_name} - {self.wing_name})" 



    
class ResidentTab(models.Model):
    r_id = models.BigAutoField(primary_key=True)
    u_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='residents')
    no_of_members = models.PositiveIntegerField()
    role = models.CharField(max_length=10, choices=[
        ('Owner', 'Owner'),
        ('Tenant', 'Tenant'),
    ])


    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    move_in = models.DateTimeField(null=True, blank=True)
    move_out = models.DateTimeField(null=True, blank=True)
    r_status = models.CharField(max_length=50, choices=[
        ('active','active'),
        ('inactive','inactive'),
    ],default='active')
    f_id = models.ForeignKey(FlatTab, on_delete=models.CASCADE)
    



    def __str__(self):
        return f"Resident {self.u_id.username} - {self.role}"  



    
class IDProof(models.Model):
    idproof = models.BigAutoField(primary_key=True)
    ID_TYPE_CHOICES = [
        ('AADHAAR', 'Aadhaar'),
        ('PASSPORT', 'Passport'),
        ('DRIVING_LICENSE', 'Driving License'),
    ]
    resident = models.ForeignKey(ResidentTab, on_delete=models.CASCADE,related_name='id_proofs' )  # Links the vehicle to a specific resident
    proof_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
    proof_number = models.CharField(max_length=20, unique=True)
    id_proof_file = models.ImageField(upload_to='id_proofs/', blank=True, null=True)

    def clean(self):
        if self.proof_type == 'AADHAAR' and not re.match(r'^\d{12}$', self.proof_number):
            raise ValidationError("Aadhaar number must be a 12-digit numeric value.")
        elif self.proof_type == 'PASSPORT' and not re.match(r'^[A-Z]{1}[0-9]{7}$', self.proof_number):
            raise ValidationError("Passport number must start with a letter followed by 7 digits.")
        elif self.proof_type == 'DRIVING_LICENSE' and not re.match(r'^[A-Z]{2}\d{13}$', self.proof_number):
            raise ValidationError("Driving License number must follow the format: 2 letters followed by 13 digits.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.proof_type} - {self.proof_number}"  

class VehicleTab(models.Model):
    v_id = models.BigAutoField(primary_key=True)  # Unique identifier for each vehicle
    resident = models.ForeignKey(ResidentTab, on_delete=models.CASCADE,related_name='vehicles' )  # Links the vehicle to a specific resident
    vehicle_type = models.CharField(max_length=50, choices=[
        ('Car', 'Car'),
        ('Bike', 'Bike'),
        ('Scooter', 'Scooter'),
        ('Other', 'Other'),
    ])
    vehicle_number = models.CharField(max_length=20, unique=True,)  # Vehicle registration number
    make_and_model = models.CharField(max_length=100, blank=True, null=True)  # Optional make/model of the vehicle
    color = models.CharField(max_length=50, blank=True, null=True)  # Optional vehicle color
    parking_slot = models.CharField(max_length=50, blank=True, null=True)  # Optional parking slot number
    registered_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the vehicle was registered
    v_status = models.CharField(max_length=50, default="active")  # Vehicle status (e.g., active, inactive)

    def clean(self):
        # Validate vehicle number format
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$', self.vehicle_number):
            raise ValidationError(
                "Vehicle number must follow the format: 2 letters (state code), "
                "2 digits (RTO code), 1-3 letters (series), and 4 digits (number). Example: KA01AB1234."
            )

    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle_type} - {self.vehicle_number} ({self.resident.u_id.username})"  


from django.utils.timezone import now

class VisitorsLog(models.Model):
    visitor_log = models.BigAutoField(primary_key=True)
    u_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visitor_logs', null=True, blank=True)
    r_id = models.ForeignKey(ResidentTab, on_delete=models.CASCADE)
    f_id = models.ForeignKey(FlatTab, on_delete=models.CASCADE, null=True, blank=True)
    visitor_name = models.CharField(max_length=30)
    visitor_email = models.EmailField(blank=True, null=True)  
    phone_no = models.CharField(max_length=10, blank=True, null=True)
    purpose_of_visit = models.CharField(max_length=255)
    group_size = models.PositiveIntegerField()
    entry_time = models.DateTimeField(default=now, blank=True)  # Auto-set when scanned
    exit_time = models.DateTimeField(null=True, blank=True)
    visitor_type = models.CharField(max_length=50)
    vehicle_number = models.CharField(max_length=20, unique=False)  # Vehicle plate number
    make_and_model = models.CharField(max_length=100, blank=True, null=True)  
    parking_slot = models.CharField(max_length=50, blank=True, null=True)  # If you want to track where they parked

    ad_approval_status = models.CharField(max_length=50)
    r_approval_status = models.CharField(max_length=50)
    visitor_status = models.CharField(max_length=50, choices=[
        ("checked_in", "checked_in"),
        ("checked_out", "checked_out"),
    ])

    

    def __str__(self):
        return f"Visitor {self.visitor_log} - {self.purpose_of_visit}"  

      
    


class AdminSettingsTab(models.Model):
    s_id = models.BigAutoField(primary_key=True)
    u_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_settings')
    entry_limit = models.PositiveIntegerField()
    notification_type = models.CharField(max_length=50)
    visitor_log = models.ForeignKey(VisitorsLog, on_delete=models.CASCADE, related_name='admin_settings', null=True, blank=True)
    auto_logout_period = models.DurationField()

    def __str__(self):
        return f"Admin Setting {self.s_id}"  


class NotificationTab(models.Model):
    n_id = models.BigAutoField(primary_key=True)
    u_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    visitor_log = models.ForeignKey(VisitorsLog, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    n_status = models.CharField(max_length=50)
    s_id = models.ForeignKey(AdminSettingsTab, on_delete=models.CASCADE, related_name='notifications')
    r_id = models.ForeignKey(ResidentTab, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Notification {self.n_id} - {self.message}"
