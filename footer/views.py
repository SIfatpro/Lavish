from django.shortcuts import render

# Create your views here.
def footer(request):
    return render(request, 'footer/templates/footer.html')