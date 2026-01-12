from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import os

@csrf_exempt
def test_database(request):
    """Test database connection - accessible via URL"""
    try:
        with connection.cursor() as cursor:
            # Test connection
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database(), current_user, now()")
            db, user, time = cursor.fetchone()
            
            return JsonResponse({
                'status': 'success',
                'database': {
                    'host': connection.settings_dict.get('HOST'),
                    'port': connection.settings_dict.get('PORT'),
                    'name': db,
                    'user': user,
                    'version': version,
                    'server_time': str(time)
                },
                'environment': {
                    'debug': os.getenv('DEBUG'),
                    'has_database_url': bool(os.getenv('DATABASE_URL')),
                    'allowed_hosts': os.getenv('ALLOWED_HOSTS', '')
                }
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__,
            'connection_info': {
                'host': connection.settings_dict.get('HOST'),
                'port': connection.settings_dict.get('PORT'),
                'name': connection.settings_dict.get('NAME'),
                'engine': connection.settings_dict.get('ENGINE')
            }
        }, status=500)