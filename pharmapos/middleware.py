import logging

logger = logging.getLogger(__name__)


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.http import Http404
        from django.core.exceptions import PermissionDenied
        from django.shortcuts import render

        if isinstance(exception, Http404):
            logger.warning("404 Not Found: %s", request.path)
            return render(request, '404.html', {'path': request.path}, status=404)

        if isinstance(exception, PermissionDenied):
            logger.warning("403 Forbidden: %s", request.path)
            return render(request, '403.html', status=403)

        logger.error("Unhandled exception on %s: %s", request.path, exception, exc_info=True)
        return render(request, '500.html', status=500)
