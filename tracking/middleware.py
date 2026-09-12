from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

class CsrfExemptMiddleware(MiddlewareMixin):
    """Middleware to exempt API endpoints from CSRF verification"""
    
    def process_request(self, request):
        # Exempt all API endpoints from CSRF verification
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None