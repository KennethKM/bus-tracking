"""
URL configuration for bus_tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.urls import include, path, reverse_lazy
from django.views.generic import TemplateView
logger = logging.getLogger(__name__)


class DiagnosticPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        users = list(super().get_users(email))

        logger.warning(
            "Password reset diagnostic: eligible_accounts=%s "
            "smtp_backend=%s smtp_host_configured=%s "
            "smtp_username_configured=%s smtp_password_configured=%s tls=%s",
            len(users),
            settings.EMAIL_BACKEND,
            bool(settings.EMAIL_HOST),
            bool(settings.EMAIL_HOST_USER),
            bool(settings.EMAIL_HOST_PASSWORD),
            settings.EMAIL_USE_TLS,
        )

        return users

    def send_mail(self, *args, **kwargs):
        logger.warning("Password reset SMTP send starting.")
        result = super().send_mail(*args, **kwargs)
        logger.warning("Password reset SMTP send completed.")
        return result

urlpatterns = [
    path(
        '',
        TemplateView.as_view(template_name='tracking/landing.html'),
        name='home',
    ),
    path(
        'passenger/',
        TemplateView.as_view(template_name='tracking/index.html'),
        name='passenger_ui',
    ),
    path(
        'driver/',
        TemplateView.as_view(template_name='tracking/driver_interface.html'),
        name='driver_ui',
    ),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=DiagnosticPasswordResetForm,
            template_name="tracking/registration/password_reset_form.html",
            email_template_name="tracking/registration/password_reset_email.txt",
            subject_template_name="tracking/registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="tracking/registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="tracking/registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="tracking/registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path('admin/', admin.site.urls),
    path('api/', include('tracking.urls')),
]
