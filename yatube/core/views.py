from django.shortcuts import render


def get_page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def get_csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')
