from django.core.management.base import BaseCommand
from apps.corecode.models import AcademicTerm

class Command(BaseCommand):
    help = 'Fix multiple current terms issue'

    def handle(self, *args, **options):
        # Find all current terms
        current_terms = AcademicTerm.objects.filter(current=True)
        
        self.stdout.write(f"Found {current_terms.count()} current terms:")
        
        for term in current_terms:
            self.stdout.write(f" - {term.name} (ID: {term.id})")
        
        if current_terms.count() > 1:
            self.stdout.write(self.style.WARNING("Multiple current terms found!"))
            
            # Keep the first one as current, set others to not current
            first_term = current_terms.first()
            terms_to_update = current_terms.exclude(id=first_term.id)
            
            updated_count = terms_to_update.update(current=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Fixed! Set {updated_count} terms to not current. "
                    f"Only '{first_term.name}' remains current."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("No issues found."))