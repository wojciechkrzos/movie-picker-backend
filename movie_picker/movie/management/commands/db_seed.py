from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help: str = "bajabongo i leszczyny"

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS("bajabongo i leszczyny"))
