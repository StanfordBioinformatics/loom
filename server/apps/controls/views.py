from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import sys
def status(request):
    return JsonResponse({}, status=200)

@csrf_exempt
def run(request):
    data = json.loads(request.body)
    return JsonResponse(data, status=200)
