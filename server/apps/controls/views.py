from django.http import JsonResponse
from django.shortcuts import render

def status(request):
    return JsonResponse({"status": "ok"}, status=200)
