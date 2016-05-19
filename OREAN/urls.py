from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^api/', include('api.urls')),
    # url(r'^OREAN/', include('OREAN.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # system monitor
    url(r'^monitorix', 'OREAN.views.monitor.resources', name='sysmonitor'),

    # GUI frontend
    url(r'^$', 'OREAN.views.home.main', name='home'),
    url(r'^entityInvestigation$', 'OREAN.views.taxaInvestigator.getRareTaxa', name='taxaInvestigator'),
    url(r'^attributes', 'OREAN.views.attributes.main', name='attributes'),
    url(r'^16sProfileBoxplot', 'OREAN.views.16sProfileBoxplot.main', name='16sProfileBoxplot'),
    url(r'^stackedbars', 'OREAN.views.stackedbars.main', name='stackedbars'),
    url(r'^ideastackedbars', 'OREAN.views.stackedbars.idea', name='ideastackedbars'),
    url(r'^clustering', 'OREAN.views.clustering.manager', name='clustering'),
    url(r'^heatmap', 'OREAN.views.heatmap.manager', name='heatmap'),
    url(r'^area', 'OREAN.views.area.main', name='area'),
    url(r'^analytics', 'OREAN.views.analytics.main', name='analytics'),
    url(r'^createProject', 'OREAN.views.createProject.main', name='createProject'), 
    url(r'^joinProject/(?P<invitecode>\w{40})', 'OREAN.views.joinProject.main', name='joinProject'), 
    url(r'^project/(?P<invitecode>\w{40})', 'OREAN.views.projectPage.main', name='projectPage'), 
    url(r'^diversity/alpha2', 'OREAN.views.diversity.alpha2', name='alpha2'),
    url(r'^diversity/alpha', 'OREAN.views.diversity.alpha', name='alpha'),
    url(r'^diversity/beta', 'OREAN.views.diversity.beta', name='beta'),
    url(r'^pca$', 'OREAN.views.pca.main', name='pca'),
    url(r'^lefse2', 'OREAN.views.lefse2.main', name='lefse2'),
    url(r'^lefse', 'OREAN.views.lefse.main', name='lefse'),
    url(r'^query/build', 'OREAN.views.buildquery.main', name='buildquery'),
    url(r'^query/merge', 'OREAN.views.buildquery.merge', name='mergequery'),
    url(r'^query/dataset', 'OREAN.views.buildquery.dataset', name='datasetquery'),
    url(r'^query/samplebased', 'OREAN.views.samplebasedquery.main', name='samplebasedquery'),
    url(r'^query/manage', 'OREAN.views.managequeries.main', name='managequeries'),
    url(r'^chooseproject', 'OREAN.views.chooseproject.main', name='chooseproject'),
    url(r'^manageProject', 'OREAN.views.manageProject.main', name='manageProject'), 
    url(r'^publicProjects', 'OREAN.views.publicProjects.enroll', name='publicProjects'), 
    url(r'^login', 'OREAN.views.login.main', name='login'),
    url(r'^logout', 'OREAN.views.logout.main', name='logout'),
    url(r'^registerNewUser', 'OREAN.views.registerNewUser.main', name='registerNewUser'),
    url(r'^activateNewUser/(?P<token>\w{32})/$', 'OREAN.views.activateNewUser.main', name='activateNewUser'),
    url(r'requestPasswordReset', 'OREAN.views.resetPassword.requestReset', name='requestReset'),
    url(r'resetPassword/(?P<token>\w{32})/$', 'OREAN.views.resetPassword.main', name='resetPassword'),
    url(r'timecourse/table', 'OREAN.views.timecourse.viewTimecourseInTable', name='timecourseTable'),
    url(r'^query/rebuild$', 'OREAN.views.buildquery.rebuild', name='rebuildquery'),

    # sample report urls
    url(r'sample/report', 'OREAN.views.samplereport.main', name='samplereport'),
    url(r'sample/fetch', 'OREAN.views.samplereport.fetchdata', name='fetchsampledata'),
    url(r'sample/krona', 'OREAN.views.samplereport.krona', name='krona'),

    # file upload
    url(r'upload/taxa', 'api.uploads.taxa.main', name='uploadTaxa'),
    url(r'upload/analysis', 'api.uploads.analysis.main', name='uploadAnalysis'),
    url(r'upload/metadata', 'api.uploads.metadata.main', name='uploadMetadata'),
    url(r'upload/status', 'api.uploads.status.main', name='uploadStatus'),

    # documentation
    url(r'^team$', TemplateView.as_view(template_name='team.html'), name='team'),
    url(r'^documentation$', TemplateView.as_view(template_name='documentation.html'), name='documentation'),
)


