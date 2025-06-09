import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Безопасно, если пароль не задан
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username=username)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Преподаватель'),
        ('student', 'Студент'),
    ]

    id = models.AutoField(primary_key=True)
   # email = models.EmailField(unique=True, blank=True, null=True)

    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)  # Новое поле
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False, verbose_name="Архивный")
    group_number = models.IntegerField(verbose_name='Номер группы', blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Отчество')

    scores = models.IntegerField(
        verbose_name='Оценка',
        blank=True,
        null=True,  # если ты хочешь разрешить пустое значение
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )
    test = models.BooleanField(default=False)
    date_of_the_test =models.DateTimeField(default=timezone.now)
    time_test = models.TimeField(default=timezone.now)


    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"{self.first_name[0].upper()}.{self.last_name}"
        super().save(*args, **kwargs)

    # def update_last_active(self):
    #     self.last_active = timezone.now()
    #     self.is_online = True
    #     self.save()

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",
        blank=True,
        help_text="Группы, к которым принадлежит пользователь."
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
        help_text="Разрешения, которые назначены пользователю."
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('start_theory', 'Начал теоретический тест'),
        ('start_practice', 'Начал практический тест'),
        ('register_student', 'Зарегистрирован студент'),
        ('login', 'Вход в систему'),
        # можешь добавить любые другие события
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Действие")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    difficulty = models.CharField(max_length=20, blank=True, null=True, verbose_name="Сложность")

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"


