# backup_manager/utils/export_utils.py
import pandas as pd
from io import BytesIO
import os
from datetime import datetime
from django.apps import apps

def get_model(app_label, model_name):
    """Safely get model class"""
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None

def export_students_excel():
    """Export all student data to Excel"""
    Student = get_model('students', 'Student')
    if not Student:
        return create_error_excel("Students app not found")
    
    try:
        students = Student.objects.all().values(
            'id', 'surname', 'firstname', 'other_name', 'gender', 
            'current_class__name', 'parent_mobile_number', 'address',
            'date_of_admission', 'current_status'
        )
        
        df = pd.DataFrame(list(students))
        df.rename(columns={
            'surname': 'Surname',
            'firstname': 'First Name', 
            'other_name': 'Other Name',
            'current_class__name': 'Class',
            'parent_mobile_number': 'Parent Phone',
            'date_of_admission': 'Admission Date',
            'current_status': 'Status'
        }, inplace=True)
        
        return create_excel_file(df, 'Students')
    except Exception as e:
        return create_error_excel(f"Error exporting students: {str(e)}")

def export_teachers_excel():
    """Export all teacher/staff data to Excel"""
    Staff = get_model('staffs', 'Staff')
    if not Staff:
        return create_error_excel("Staffs app not found")
    
    try:
        # Using the actual field names from your error message
        teachers = Staff.objects.all().values(
            'id', 'surname', 'firstname', 'other_name', 'gender',
            'mobile_number', 'address', 'date_of_birth', 'current_status'
        )
        
        df = pd.DataFrame(list(teachers))
        df.rename(columns={
            'surname': 'Surname',
            'firstname': 'First Name',
            'other_name': 'Other Name', 
            'mobile_number': 'Phone Number',
            'current_status': 'Status'
        }, inplace=True)
        
        return create_excel_file(df, 'Teachers & Staff')
    except Exception as e:
        return create_error_excel(f"Error exporting teachers: {str(e)}")

def export_finance_excel():
    """Export financial data to Excel with multiple sheets"""
    Invoice = get_model('finance', 'Invoice')
    Receipt = get_model('finance', 'Receipt')
    InvoiceItem = get_model('finance', 'InvoiceItem')
    
    if not Invoice or not Receipt:
        return create_error_excel("Finance app not found")
    
    try:
        # Invoice data
        invoices = Invoice.objects.all().values(
            'id', 'student__surname', 'student__firstname', 'session__name',
            'term__name', 'class_for__name', 'balance', 'status'
        )
        
        df_invoices = pd.DataFrame(list(invoices))
        df_invoices.rename(columns={
            'student__surname': 'Student Surname',
            'student__firstname': 'Student First Name',
            'session__name': 'Academic Session',
            'term__name': 'Academic Term',
            'class_for__name': 'Class'
        }, inplace=True)
        
        # Receipt data
        receipts = Receipt.objects.all().values(
            'id', 'invoice__student__surname', 'invoice__student__firstname',
            'amount_paid', 'date_paid', 'comment'
        )
        
        df_receipts = pd.DataFrame(list(receipts))
        df_receipts.rename(columns={
            'invoice__student__surname': 'Student Surname',
            'invoice__student__firstname': 'Student First Name',
            'amount_paid': 'Amount Paid',
            'date_paid': 'Payment Date'
        }, inplace=True)
        
        # Invoice Items if available
        df_items = pd.DataFrame()
        if InvoiceItem:
            items = InvoiceItem.objects.all().values(
                'invoice__id', 'description', 'amount'
            )
            df_items = pd.DataFrame(list(items))
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_invoices.to_excel(writer, sheet_name='Invoices', index=False)
            df_receipts.to_excel(writer, sheet_name='Receipts', index=False)
            if not df_items.empty:
                df_items.to_excel(writer, sheet_name='Invoice Items', index=False)
            
            # Auto-adjust columns for all sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    except Exception as e:
        return create_error_excel(f"Error exporting finance: {str(e)}")

def export_academic_data():
    """Export academic data - sessions, terms, subjects, classes"""
    AcademicSession = get_model('corecode', 'AcademicSession')
    AcademicTerm = get_model('corecode', 'AcademicTerm')
    Subject = get_model('corecode', 'Subject')
    StudentClass = get_model('corecode', 'StudentClass')
    
    if not all([AcademicSession, AcademicTerm, Subject, StudentClass]):
        return create_error_excel("Corecode app not found")
    
    try:
        # Academic Sessions
        sessions = AcademicSession.objects.all().values('id', 'name', 'current')
        df_sessions = pd.DataFrame(list(sessions))
        df_sessions.rename(columns={'current': 'Is Current'}, inplace=True)
        
        # Academic Terms  
        terms = AcademicTerm.objects.all().values('id', 'name', 'current')
        df_terms = pd.DataFrame(list(terms))
        df_terms.rename(columns={'current': 'Is Current'}, inplace=True)
        
        # Subjects
        subjects = Subject.objects.all().values('id', 'name')
        df_subjects = pd.DataFrame(list(subjects))
        
        # Student Classes
        classes = StudentClass.objects.all().values('id', 'name')
        df_classes = pd.DataFrame(list(classes))
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_sessions.to_excel(writer, sheet_name='Academic Sessions', index=False)
            df_terms.to_excel(writer, sheet_name='Academic Terms', index=False)
            df_subjects.to_excel(writer, sheet_name='Subjects', index=False)
            df_classes.to_excel(writer, sheet_name='Classes', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    except Exception as e:
        return create_error_excel(f"Error exporting academic data: {str(e)}")

def export_results_excel():
    """Export student results"""
    Result = get_model('result', 'Result')
    if not Result:
        return create_error_excel("Result app not found")
    
    try:
        results = Result.objects.all().values(
            'student__surname', 'student__firstname', 'session__name',
            'term__name', 'subject__name', 'test_score', 'exam_score',
            'total_score', 'grade'
        )
        
        df = pd.DataFrame(list(results))
        df.rename(columns={
            'student__surname': 'Student Surname',
            'student__firstname': 'Student First Name', 
            'session__name': 'Academic Session',
            'term__name': 'Academic Term',
            'subject__name': 'Subject',
            'test_score': 'Test Score',
            'exam_score': 'Exam Score', 
            'total_score': 'Total Score'
        }, inplace=True)
        
        return create_excel_file(df, 'Results')
    except Exception as e:
        return create_error_excel(f"Error exporting results: {str(e)}")

def export_attendance_excel():
    """Export attendance data"""
    AttendanceRegister = get_model('attendance', 'AttendanceRegister')
    AttendanceEntry = get_model('attendance', 'AttendanceEntry')
    
    if not AttendanceRegister or not AttendanceEntry:
        return create_error_excel("Attendance app not found")
    
    try:
        # Attendance Registers
        registers = AttendanceRegister.objects.all().values(
            'name', 'class__name', 'session__name', 'term__name', 'date'
        )
        
        df_registers = pd.DataFrame(list(registers))
        df_registers.rename(columns={
            'class__name': 'Class',
            'session__name': 'Academic Session',
            'term__name': 'Academic Term'
        }, inplace=True)
        
        # Attendance Entries
        entries = AttendanceEntry.objects.all().values(
            'register__name', 'student__surname', 'student__firstname',
            'status', 'date'
        )
        
        df_entries = pd.DataFrame(list(entries))
        df_entries.rename(columns={
            'register__name': 'Register Name',
            'student__surname': 'Student Surname',
            'student__firstname': 'Student First Name'
        }, inplace=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_registers.to_excel(writer, sheet_name='Attendance Registers', index=False)
            df_entries.to_excel(writer, sheet_name='Attendance Entries', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    except Exception as e:
        return create_error_excel(f"Error exporting attendance: {str(e)}")

def export_idcards_excel():
    """Export ID card data"""
    StudentIDCard = get_model('idcards', 'StudentIDCard')
    TeacherIDCard = get_model('idcards', 'TeacherIDCard')
    
    if not StudentIDCard and not TeacherIDCard:
        return create_error_excel("ID Cards app not found")
    
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            if StudentIDCard:
                student_cards = StudentIDCard.objects.all().values(
                    'student__surname', 'student__firstname', 'student__current_class__name',
                    'issue_date', 'expiry_date'
                )
                df_students = pd.DataFrame(list(student_cards))
                df_students.rename(columns={
                    'student__surname': 'Student Surname',
                    'student__firstname': 'Student First Name',
                    'student__current_class__name': 'Class'
                }, inplace=True)
                df_students.to_excel(writer, sheet_name='Student ID Cards', index=False)
            
            if TeacherIDCard:
                # Using available fields - removed 'position' since it doesn't exist
                teacher_cards = TeacherIDCard.objects.all().values(
                    'teacher__surname', 'teacher__firstname',
                    'issue_date', 'expiry_date'
                )
                df_teachers = pd.DataFrame(list(teacher_cards))
                df_teachers.rename(columns={
                    'teacher__surname': 'Teacher Surname',
                    'teacher__firstname': 'Teacher First Name'
                }, inplace=True)
                df_teachers.to_excel(writer, sheet_name='Teacher ID Cards', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    except Exception as e:
        return create_error_excel(f"Error exporting ID cards: {str(e)}")

# backup_manager/utils/export_utils.py

def export_portfolio_excel():
    """Export student portfolio data"""
    PortfolioCategory = get_model('student_portfolio', 'PortfolioCategory')
    PortfolioItem = get_model('student_portfolio', 'PortfolioItem')
    
    if not PortfolioCategory and not PortfolioItem:
        return create_error_excel("Student Portfolio app not found")
    
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            if PortfolioCategory:
                categories = PortfolioCategory.objects.all().values('name', 'description')
                df_categories = pd.DataFrame(list(categories))
                df_categories.to_excel(writer, sheet_name='Portfolio Categories', index=False)
            
            if PortfolioItem:
                # Get the data first, then process datetime fields
                items = PortfolioItem.objects.all().values(
                    'student__surname', 'student__firstname', 'category__name',
                    'title', 'description', 'created_at', 'updated_at'
                )
                
                # Convert to DataFrame
                df_items = pd.DataFrame(list(items))
                
                # Convert timezone-aware datetimes to timezone-naive
                if 'created_at' in df_items.columns and not df_items.empty:
                    df_items['created_at'] = df_items['created_at'].apply(
                        lambda x: x.replace(tzinfo=None) if x and x.tzinfo else x
                    )
                
                if 'updated_at' in df_items.columns and not df_items.empty:
                    df_items['updated_at'] = df_items['updated_at'].apply(
                        lambda x: x.replace(tzinfo=None) if x and x.tzinfo else x
                    )
                
                df_items.rename(columns={
                    'student__surname': 'Student Surname',
                    'student__firstname': 'Student First Name',
                    'category__name': 'Category',
                    'created_at': 'Date Created',
                    'updated_at': 'Last Updated'
                }, inplace=True)
                df_items.to_excel(writer, sheet_name='Portfolio Items', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min((max_length + 2), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    except Exception as e:
        return create_error_excel(f"Error exporting portfolio: {str(e)}")

def create_excel_file(df, sheet_name):
    """Helper function to create Excel file from DataFrame"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets[sheet_name]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min((max_length + 2), 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output

def create_error_excel(error_message):
    """Create an Excel file with error message"""
    df = pd.DataFrame({
        'Error': [error_message],
        'Solution': ['Please check if the app is installed and models exist']
    })
    return create_excel_file(df, 'Error')

def export_all_data():
    """Export all school data to separate Excel files"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    export_dir = f"exports/{timestamp}"
    
    print(f"🔄 Starting export to: {export_dir}")
    
    try:
        os.makedirs(export_dir, exist_ok=True)
        print(f"✅ Created directory: {export_dir}")
        
        export_results = {}
        
        # Export each data type with error handling
        try:
            print("🔄 Exporting students...")
            students_file = export_students_excel()
            students_path = f"{export_dir}/01_students.xlsx"
            with open(students_path, "wb") as f:
                f.write(students_file.getvalue())
            export_results['students'] = 'Success'
            print(f"✅ Students exported: {students_path}")
        except Exception as e:
            export_results['students'] = f'Failed: {str(e)}'
            print(f"❌ Students export failed: {str(e)}")
        
        try:
            print("🔄 Exporting teachers...")
            teachers_file = export_teachers_excel()
            teachers_path = f"{export_dir}/02_teachers_staff.xlsx"
            with open(teachers_path, "wb") as f:
                f.write(teachers_file.getvalue())
            export_results['teachers'] = 'Success'
            print(f"✅ Teachers exported: {teachers_path}")
        except Exception as e:
            export_results['teachers'] = f'Failed: {str(e)}'
            print(f"❌ Teachers export failed: {str(e)}")
        
        try:
            print("🔄 Exporting finance...")
            finance_file = export_finance_excel()
            finance_path = f"{export_dir}/03_finance.xlsx"
            with open(finance_path, "wb") as f:
                f.write(finance_file.getvalue())
            export_results['finance'] = 'Success'
            print(f"✅ Finance exported: {finance_path}")
        except Exception as e:
            export_results['finance'] = f'Failed: {str(e)}'
            print(f"❌ Finance export failed: {str(e)}")
        
        try:
            print("🔄 Exporting academic data...")
            academic_file = export_academic_data()
            academic_path = f"{export_dir}/04_academic_data.xlsx"
            with open(academic_path, "wb") as f:
                f.write(academic_file.getvalue())
            export_results['academic'] = 'Success'
            print(f"✅ Academic data exported: {academic_path}")
        except Exception as e:
            export_results['academic'] = f'Failed: {str(e)}'
            print(f"❌ Academic data export failed: {str(e)}")
        
        try:
            print("🔄 Exporting results...")
            results_file = export_results_excel()
            results_path = f"{export_dir}/05_results.xlsx"
            with open(results_path, "wb") as f:
                f.write(results_file.getvalue())
            export_results['results'] = 'Success'
            print(f"✅ Results exported: {results_path}")
        except Exception as e:
            export_results['results'] = f'Failed: {str(e)}'
            print(f"❌ Results export failed: {str(e)}")
        
        try:
            print("🔄 Exporting attendance...")
            attendance_file = export_attendance_excel()
            attendance_path = f"{export_dir}/06_attendance.xlsx"
            with open(attendance_path, "wb") as f:
                f.write(attendance_file.getvalue())
            export_results['attendance'] = 'Success'
            print(f"✅ Attendance exported: {attendance_path}")
        except Exception as e:
            export_results['attendance'] = f'Failed: {str(e)}'
            print(f"❌ Attendance export failed: {str(e)}")
        
        try:
            print("🔄 Exporting ID cards...")
            idcards_file = export_idcards_excel()
            idcards_path = f"{export_dir}/07_id_cards.xlsx"
            with open(idcards_path, "wb") as f:
                f.write(idcards_file.getvalue())
            export_results['idcards'] = 'Success'
            print(f"✅ ID Cards exported: {idcards_path}")
        except Exception as e:
            export_results['idcards'] = f'Failed: {str(e)}'
            print(f"❌ ID Cards export failed: {str(e)}")
        
        try:
            print("🔄 Exporting portfolio...")
            portfolio_file = export_portfolio_excel()
            portfolio_path = f"{export_dir}/08_portfolio.xlsx"
            with open(portfolio_path, "wb") as f:
                f.write(portfolio_file.getvalue())
            export_results['portfolio'] = 'Success'
            print(f"✅ Portfolio exported: {portfolio_path}")
        except Exception as e:
            export_results['portfolio'] = f'Failed: {str(e)}'
            print(f"❌ Portfolio export failed: {str(e)}")
        
        print(f"🎉 Export process completed. Results: {export_results}")
        
        # Check if any exports succeeded
        success_count = sum(1 for result in export_results.values() if result == 'Success')
        if success_count > 0:
            return export_dir, True, export_results
        else:
            return "All exports failed", False, export_results
        
    except Exception as e:
        print(f"❌ Export process failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return str(e), False, export_results