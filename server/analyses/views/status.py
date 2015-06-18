from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)
