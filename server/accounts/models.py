from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        HR = "HR", "HR"
        EMPLOYEE = "EMPLOYEE", "Employee"

    username = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    photo = models.ImageField(upload_to='user_photos/')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    company = models.ForeignKey("feedback.Company", on_delete=models.PROTECT, related_name="users", null=True, blank=True)
    department = models.ForeignKey("feedback.Department", on_delete=models.PROTECT, related_name="users", null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"

    def __str__(self):
        return self.username
