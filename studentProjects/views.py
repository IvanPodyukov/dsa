from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def main(request):
    return render(request, 'common/main.html')
