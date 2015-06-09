from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from api.models import *

#@csrf_protect
@csrf_exempt
def main(request):
    username = password = mynext = firstname = ''
    mynext = request.GET.get('next') or None
    if mynext is None: mynext = 'managequeries'
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        mynext = request.POST.get('next') or None
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                ap = ActiveProject.objects.get_or_none(user=user)
                if ap is None: return redirect('chooseproject')
                request.session['projectID'] = ap.project.pk
                request.session['projectName'] = ap.project.name
                messages.add_message(request, messages.INFO, "Active project: %s." % ap.project.name)
                return redirect(mynext)
            else:
                messages.add_message(request, messages.ERROR, "This account is not active. Please verify your account by visiting the URL provided in the registration email.")
        else:
            messages.add_message(request, messages.ERROR, "Your login credentials are incorrect.")
    params = {
        'username' : username,
        'firstname': firstname,
        'next': mynext,
    }
    return render(request, 'login.html', params)
