from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    # Your logic here (e.g., loading data for the dashboard)
    return render(request, 'dashboard.html')
