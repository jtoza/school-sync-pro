import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime, parse_date, parse_time
from django.db import IntegrityError
from apps.students.models import Student
from apps.staffs.models import Staff, TeacherAttendance
from apps.result.models import Result
from apps.finance.models import Invoice, InvoiceItem, Receipt
from apps.idcards.models import StudentIDCard, TeacherIDCard

@method_decorator(csrf_exempt, name='dispatch')
class SyncData(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
            pending_changes = data.get('changes', [])
            last_sync = data.get('last_sync')
            
            print(f"📥 Received sync request from device: {device_id}")
            print(f"📦 Pending changes: {len(pending_changes)}")
            
            # Process client changes
            processed_changes = []
            for change in pending_changes:
                result = self.process_client_change(change, device_id)
                if result:
                    processed_changes.append(result)
            
            # Get server changes since last sync
            server_changes = []
            if last_sync:
                server_changes = self.get_server_changes_since(last_sync)
            
            response_data = {
                'status': 'success',
                'processed_changes': processed_changes,
                'server_changes': server_changes,
                'server_time': timezone.now().isoformat(),
                'message': f'Processed {len(processed_changes)} changes, sent {len(server_changes)} server changes'
            }
            
            print(f"📤 Sync response: {response_data['message']}")
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ Sync error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    def process_client_change(self, change, device_id):
        model_name = change['model']
        operation = change['operation']
        data = change['data']
        
        try:
            with transaction.atomic():
                if model_name == 'student':
                    return self.process_student_change(operation, data, device_id)
                elif model_name == 'staff':
                    return self.process_staff_change(operation, data, device_id)
                elif model_name == 'teacher_attendance':
                    return self.process_teacher_attendance_change(operation, data, device_id)
                elif model_name == 'result':
                    return self.process_result_change(operation, data, device_id)
                elif model_name == 'invoice':
                    return self.process_invoice_change(operation, data, device_id)
                elif model_name == 'invoice_item':
                    return self.process_invoice_item_change(operation, data, device_id)
                elif model_name == 'receipt':
                    return self.process_receipt_change(operation, data, device_id)
                elif model_name == 'student_id_card':
                    return self.process_student_id_card_change(operation, data, device_id)
                elif model_name == 'teacher_id_card':
                    return self.process_teacher_id_card_change(operation, data, device_id)
                else:
                    print(f"⚠️ Unknown model: {model_name}")
                    return None
                
        except Exception as e:
            print(f"❌ Error processing {model_name} change: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
def process_teacher_attendance_change(self, operation, data, device_id):
    print(f"🔄 Processing teacher_attendance {operation}: {data}")
    
    if operation == 'create':
        # Check if already exists by sync_id
        if TeacherAttendance.objects.filter(sync_id=data['sync_id']).exists():
            print(f"⚠️ Already exists by sync_id: {data['sync_id']}")
            return None
        
        # Get teacher - for testing, use first available teacher
        try:
            teacher = Staff.objects.first()
            if not teacher:
                print("❌ No teachers found in database")
                return None
            
            # Handle time fields - convert string to time object if needed
            time_in = data.get('time_in')
            time_out = data.get('time_out')
            
            # If time_in/time_out are strings, parse them
            if time_in and isinstance(time_in, str):
                time_in = parse_time(time_in)
            if time_out and isinstance(time_out, str):
                time_out = parse_time(time_out)
            
            try:
                # Try to create the attendance record
                attendance = TeacherAttendance.objects.create(
                    teacher=teacher,
                    date=data['date'],
                    status=data['status'],
                    time_in=time_in,
                    time_out=time_out,
                    notes=data.get('notes', ''),
                    sync_id=data['sync_id'],
                    sync_status='synced',
                    device_id=device_id
                )
                print(f"✅ Created teacher attendance: {attendance}")
                return self.serialize_teacher_attendance(attendance, 'create')
                
            except IntegrityError:
                # Handle unique constraint violation - update existing record instead
                print(f"⚠️ Attendance already exists for {teacher} on {data['date']}, updating instead")
                
                # Get the existing record
                existing_attendance = TeacherAttendance.objects.get(
                    teacher=teacher, 
                    date=data['date']
                )
                
                # Update the existing record
                existing_attendance.status = data['status']
                existing_attendance.time_in = time_in
                existing_attendance.time_out = time_out
                existing_attendance.notes = data.get('notes', existing_attendance.notes)
                existing_attendance.sync_id = data['sync_id']  # Update sync_id to new one
                existing_attendance.sync_status = 'synced'
                existing_attendance.device_id = device_id
                existing_attendance.save()
                
                print(f"✅ Updated existing teacher attendance: {existing_attendance}")
                return self.serialize_teacher_attendance(existing_attendance, 'update')
                
        except TeacherAttendance.DoesNotExist:
            print(f"❌ Existing attendance not found for update")
            return None
        except Exception as e:
            print(f"❌ Error processing teacher attendance: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
    elif operation == 'update':
        try:
            attendance = TeacherAttendance.objects.get(sync_id=data['sync_id'])
            attendance.date = data.get('date', attendance.date)
            attendance.status = data.get('status', attendance.status)
            
            # Handle time fields
            time_in = data.get('time_in')
            time_out = data.get('time_out')
            if time_in and isinstance(time_in, str):
                attendance.time_in = parse_time(time_in)
            elif time_in is not None:
                attendance.time_in = time_in
                
            if time_out and isinstance(time_out, str):
                attendance.time_out = parse_time(time_out)
            elif time_out is not None:
                attendance.time_out = time_out
            
            attendance.notes = data.get('notes', attendance.notes)
            attendance.sync_status = 'synced'
            attendance.save()
            
            print(f"✅ Updated teacher attendance: {attendance}")
            return self.serialize_teacher_attendance(attendance, 'update')
            
        except TeacherAttendance.DoesNotExist:
            print(f"❌ TeacherAttendance not found: {data['sync_id']}")
            return None
        except Exception as e:
            print(f"❌ Error updating teacher attendance: {e}")
            return None
    else:
        print(f"⚠️ Unknown operation: {operation}")
        return None

    def process_staff_change(self, operation, data, device_id):
        print(f"Processing staff {operation}: {data}")
        # For now, return None - implement later
        return None

    def process_student_change(self, operation, data, device_id):
        print(f"Processing student {operation}: {data}")
        # For now, return None - implement later
        return None

    def process_result_change(self, operation, data, device_id):
        print(f"Processing result {operation}: {data}")
        # For now, return None - implement later
        return None

    def process_invoice_change(self, operation, data, device_id):
        print(f"Processing invoice {operation}: {data}")
        return None

    def process_invoice_item_change(self, operation, data, device_id):
        print(f"Processing invoice_item {operation}: {data}")
        return None

    def process_receipt_change(self, operation, data, device_id):
        print(f"Processing receipt {operation}: {data}")
        return None

    def process_student_id_card_change(self, operation, data, device_id):
        print(f"Processing student_id_card {operation}: {data}")
        return None

    def process_teacher_id_card_change(self, operation, data, device_id):
        print(f"Processing teacher_id_card {operation}: {data}")
        return None

    def get_server_changes_since(self, last_sync):
        changes = []
        
        # Parse the last_sync string to datetime
        try:
            last_sync_dt = parse_datetime(last_sync)
            if not last_sync_dt:
                print(f"❌ Could not parse last_sync: {last_sync}")
                return changes
        except Exception as e:
            print(f"❌ Error parsing last_sync: {e}")
            return changes
        
        # Get teacher attendance changes
        try:
            attendances = TeacherAttendance.objects.filter(last_modified__gt=last_sync_dt)
            for attendance in attendances:
                changes.append(self.serialize_teacher_attendance(attendance, 'update'))
            print(f"📤 Found {len(attendances)} server changes since {last_sync}")
        except Exception as e:
            print(f"❌ Error getting server changes: {e}")
        
        return changes

    def serialize_teacher_attendance(self, attendance, operation):
        try:
            # Safely handle the last_modified field
            if hasattr(attendance.last_modified, 'isoformat'):
                last_modified_iso = attendance.last_modified.isoformat()
            else:
                # If it's already a string or None, use as is
                last_modified_iso = str(attendance.last_modified) if attendance.last_modified else None
            
            # Safely handle the date field
            if hasattr(attendance.date, 'isoformat'):
                date_iso = attendance.date.isoformat()
            else:
                date_iso = str(attendance.date) if attendance.date else None
            
            serialized_data = {
                'model': 'teacher_attendance',
                'operation': operation,
                'data': {
                    'id': attendance.id,
                    'sync_id': str(attendance.sync_id),
                    'teacher_sync_id': str(attendance.teacher.sync_id) if attendance.teacher and attendance.teacher.sync_id else None,
                    'date': date_iso,
                    'status': attendance.status,
                    'time_in': str(attendance.time_in) if attendance.time_in else None,
                    'time_out': str(attendance.time_out) if attendance.time_out else None,
                    'notes': attendance.notes,
                    'sync_status': attendance.sync_status,
                    'last_modified': last_modified_iso
                }
            }
            return serialized_data
            
        except Exception as e:
            print(f"❌ Error serializing teacher attendance: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    def serialize_staff(self, staff, operation):
        return {
            'model': 'staff',
            'operation': operation,
            'data': {
                'id': staff.id,
                'sync_id': str(staff.sync_id),
                'surname': staff.surname,
                'firstname': staff.firstname,
                'other_name': staff.other_name,
                'last_modified': staff.last_modified.isoformat() if hasattr(staff.last_modified, 'isoformat') else str(staff.last_modified)
            }
        }

    def serialize_student(self, student, operation):
        return {
            'model': 'student',
            'operation': operation,
            'data': {
                'id': student.id,
                'sync_id': str(student.sync_id),
                'registration_number': student.registration_number,
                'surname': student.surname,
                'firstname': student.firstname,
                'last_modified': student.last_modified.isoformat() if hasattr(student.last_modified, 'isoformat') else str(student.last_modified)
            }
        }

    def serialize_result(self, result, operation):
        return {
            'model': 'result',
            'operation': operation,
            'data': {
                'id': result.id,
                'sync_id': str(result.sync_id),
                'student_sync_id': str(result.student.sync_id),
                'test_score': result.test_score,
                'exam_score': result.exam_score,
                'last_modified': result.last_modified.isoformat() if hasattr(result.last_modified, 'isoformat') else str(result.last_modified)
            }
        }