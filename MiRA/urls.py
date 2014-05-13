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
    url(r'^area$', 'MiRA.views.area.main', name='area'),
    url(r'^diversity/alpha$', 'MiRA.views.diversity.alpha', name='alpha'),
    url(r'^diversity/beta$', 'MiRA.views.diversity.beta', name='beta'),
    url(r'^pca$', 'MiRA.views.pca.main', name='pca'),
    url(r'^buildquery$', 'MiRA.views.buildquery.main', name='buildquery'),
    url(r'^samplebasedquery$', 'MiRA.views.samplebasedquery.main', name='samplebasedquery'),
    url(r'^managequeries$', 'MiRA.views.managequeries.main', name='managequeries'),
    url(r'^login$', 'MiRA.views.login.main', name='login'),
    url(r'^logout$', 'MiRA.views.logout.main', name='logout'),
)
