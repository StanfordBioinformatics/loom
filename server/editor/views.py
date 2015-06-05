from django.shortcuts import render

# Create your views here.
def index(request):
    html = "<html><body>It works!</body></html>"
    return render(request, 'editor/index.html')
