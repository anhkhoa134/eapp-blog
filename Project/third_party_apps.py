from django.apps import AppConfig


class TemplatedEmailConfig(AppConfig):
    # Match the vendor's existing AutoField migration under Django 5.2.
    name = "templated_email"
    default_auto_field = "django.db.models.AutoField"
