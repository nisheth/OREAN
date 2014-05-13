from django.contrib import admin
from api.models import *

class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name']
class UserProjectAdmin(admin.ModelAdmin):
    list_display = ['user', 'project']

admin.site.register(Project, ProjectAdmin)
admin.site.register(UserProject, UserProjectAdmin)
