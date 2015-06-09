from django.shortcuts import redirect
from django.contrib.auth import logout

def main(request):
    request.session.flush()
    logout(request)
    return redirect('home')
