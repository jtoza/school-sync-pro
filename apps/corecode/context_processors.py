from .models import AcademicSession, AcademicTerm, SiteConfig

def site_defaults(request):
    contexts = {}
    
    # Safely get current session - with multiple exception handling
    try:
        current_session = AcademicSession.objects.get(current=True)
        contexts["current_session"] = current_session.name
    except AcademicSession.DoesNotExist:
        contexts["current_session"] = "No Session Set"
    except Exception as e:
        contexts["current_session"] = "No Session Set"

    # Safely get current term - with multiple exception handling
    try:
        current_term = AcademicTerm.objects.get(current=True)
        contexts["current_term"] = current_term.name
    except AcademicTerm.DoesNotExist:
        contexts["current_term"] = "No Term Set"
    except Exception as e:
        contexts["current_term"] = "No Term Set"

    # Safely get site config
    try:
        vals = SiteConfig.objects.all()
        for val in vals:
            contexts[val.key] = val.value
    except Exception as e:
        pass  # Ignore all site config errors

    return contexts