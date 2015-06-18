from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from analyses.models import AnalysisRequest

@csrf_exempt
@require_http_methods(["POST"])
def create(request):
    data_json = request.body
    try:
        analysis_request = AnalysisRequest.create(data_json)
        return JsonResponse({"message": "created analysis request _id=%s" % analysis_request._id}, status=201)
    except Exception as e:
        return JsonResponse({"message": e}, status=500)

