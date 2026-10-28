from datetime import date

from django.core.management.base import BaseCommand, CommandError

from simulation.fixtures.demo_data import seed_demo_data


class Command(BaseCommand):
    help = (
        "Seed deterministic, clearly simulated demo users, workspaces, social "
        "accounts, posts, daily insights, and comments. Safe to run repeatedly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reference-date",
            type=str,
            default=None,
            help="Anchor date in YYYY-MM-DD format (defaults to today).",
        )

    def handle(self, *args, **options):
        reference = date.today()
        if options.get("reference_date"):
            try:
                reference = date.fromisoformat(options["reference_date"])
            except ValueError as exc:
                raise CommandError("--reference-date must be YYYY-MM-DD.") from exc

        counts = seed_demo_data(reference)
        self.stdout.write(self.style.SUCCESS("Simulated demo data seeded."))
        for key, value in counts.items():
            self.stdout.write(f"  {key}: {value}")
        self.stdout.write(
            "  All social metrics and comments are simulated; no Instagram API "
            "was contacted."
        )
