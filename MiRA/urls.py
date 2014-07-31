from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^api/', include('api.urls')),
    # url(r'^MiRA/', include('MiRA.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # GUI frontend
    url(r'^$', 'MiRA.views.home.main', name='home'),
    url(r'^attributes', 'MiRA.views.attributes.main', name='attributes'),
    url(r'^16sProfileBoxplot', 'MiRA.views.16sProfileBoxplot.main', name='16sProfileBoxplot'),
    url(r'^area', 'MiRA.views.area.main', name='area'),
    url(r'^analytics', 'MiRA.views.analytics.main', name='analytics'),
    url(r'^createProject', 'MiRA.views.createProject.main', name='createProject'), 
    url(r'^diversity/alpha', 'MiRA.views.diversity.alpha', name='alpha'),
    url(r'^diversity/beta', 'MiRA.views.diversity.beta', name='beta'),
    url(r'^pca$', 'MiRA.views.pca.main', name='pca'),
    url(r'^buildquery', 'MiRA.views.buildquery.main', name='buildquery'),
    url(r'^datasetquery', 'MiRA.views.buildquery.dataset', name='datasetquery'),
    url(r'^chooseproject', 'MiRA.views.chooseproject.main', name='chooseproject'),
    url(r'^samplebasedquery', 'MiRA.views.samplebasedquery.main', name='samplebasedquery'),
    url(r'^managequeries', 'MiRA.views.managequeries.main', name='managequeries'),
    url(r'^manageProject', 'MiRA.views.manageProject.main', name='manageProject'), 
    url(r'^login', 'MiRA.views.login.main', name='login'),
    url(r'^logout', 'MiRA.views.logout.main', name='logout'),
    url(r'^registerNewUser', 'MiRA.views.registerNewUser.main', name='registerNewUser'),
    url(r'^activateNewUser/(?P<token>\w{32})/$', 'MiRA.views.activateNewUser.main', name='activateNewUser'),
    url(r'requestPasswordReset', 'MiRA.views.resetPassword.requestReset', name='requestReset'),
    url(r'resetPassword/(?P<token>\w{32})/$', 'MiRA.views.resetPassword.main', name='resetPassword'),
)
