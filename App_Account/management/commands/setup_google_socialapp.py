import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Tự động tạo/cập nhật SocialApp Google cho django-allauth"

    def add_arguments(self, parser):
        parser.add_argument("--client-id", dest="client_id", default=None)
        parser.add_argument("--secret", dest="secret", default=None)
        parser.add_argument("--site-id", dest="site_id", type=int, default=getattr(settings, "SITE_ID", 1))
        parser.add_argument("--site-domain", dest="site_domain", default=None)
        parser.add_argument("--site-name", dest="site_name", default=None)

    def handle(self, *args, **options):
        client_id = options["client_id"] or os.getenv("GOOGLE_CLIENT_ID")
        secret = options["secret"] or os.getenv("GOOGLE_CLIENT_SECRET")
        site_id = options["site_id"]
        site_domain = options["site_domain"] or os.getenv("DOMAIN") or "127.0.0.1:8000"
        site_name = options["site_name"] or site_domain

        if not client_id or not secret:
            raise CommandError(
                "Thiếu GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET. "
                "Hãy set env hoặc truyền --client-id và --secret."
            )

        site, site_created = Site.objects.update_or_create(
            id=site_id,
            defaults={"domain": site_domain, "name": site_name},
        )
        if site_created:
            self.stdout.write(self.style.SUCCESS(f"Da tao Site id={site.id} ({site.domain})"))
        else:
            self.stdout.write(self.style.WARNING(f"Da cap nhat Site id={site.id} ({site.domain})"))

        app, app_created = SocialApp.objects.get_or_create(
            provider="google",
            defaults={
                "name": "Google OAuth",
                "client_id": client_id,
                "secret": secret,
            },
        )

        app.name = "Google OAuth"
        app.client_id = client_id
        app.secret = secret
        app.save()
        app.sites.add(site)

        if app_created:
            self.stdout.write(self.style.SUCCESS("Da tao SocialApp provider=google"))
        else:
            self.stdout.write(self.style.WARNING("Da cap nhat SocialApp provider=google"))

        self.stdout.write(self.style.SUCCESS("Hoan tat cau hinh Google SocialApp."))
