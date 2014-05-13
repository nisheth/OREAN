from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

@csrf_protect
def main(request):
    username = password = mynext = firstname = ''
    mynext = request.GET.get('next') or 'home'
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        mynext = request.POST.get('next') or 'home'
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(mynext)
            else:
                messages.add_message(request, messages.INFO, "This account is not allowed to log in.")
        else:
            messages.add_message(request, messages.INFO, "Your login credentials are incorrect.")
    params = {
        'username' : username,
        'firstname': firstname,
        'next': mynext,
    }
    return render(request, 'login.html', params)
