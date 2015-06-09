from api.models import *

class KeyCheck(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        #key = request.GET.get('key') or None
        #print 'FIFIIFIIFIF'
        #try: request.user = CustomUser.objects.get(apikey=key)
        #except: pass
        return None
