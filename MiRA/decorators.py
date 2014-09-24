from django.shortcuts import redirect

def activeproject(view_func):

    def _wrapped_view_func(request, *args, **kwargs):

        if not 'projectID' in request.session:
            return redirect('chooseproject')

        return view_func(request, *args, **kwargs)
    return _wrapped_view_func
