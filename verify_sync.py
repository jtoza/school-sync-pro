import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

from apps.sync.views import SyncData

print("Verifying SyncData class structure...")

view = SyncData()

methods_to_check = [
    'process_teacher_attendance_change',
    'process_staff_change',
    'process_student_change',
    'get_server_changes_since'
]

all_passed = True
for method in methods_to_check:
    if hasattr(view, method):
        print(f"OK: {method} exists in SyncData")
    else:
        print(f"FAIL: {method} MISSING in SyncData")
        all_passed = False

if all_passed:
    print("\nSUCCESS: SyncData class structure is correct.")
else:
    print("\nFAILURE: SyncData class structure is incorrect.")
    print("\nAvailable attributes in SyncData:")
    print(dir(SyncData))
