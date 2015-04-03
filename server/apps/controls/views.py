import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .helpers.runrequest import RunRequestHelper
from .helpers.runrequest import RunRequestValidationError
#from apps.analysis.models import AnalysisRequest

def status(request):
    return JsonResponse({}, status=200)

@csrf_exempt
def run(request):
    data_json = request.body
    try:
        data = json.loads(data_json)
    except ValueError:
        return JsonResponse({"message": 'Error: Input is not in valid JSON format: "%s"' % request.body}, status=400)

    try:
        clean_data_json = RunRequestHelper.clean_json(data_json)
    except RunRequestValidationError as e:
        return JsonResponse({"message": 'Error validating the run request. "%s"' % e.message}, status=400)

    # AnalysisRequest.create(clean_data_json)
    return JsonResponse({"message": "A valid analysis run request was received."}, status=200)
