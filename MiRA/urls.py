from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView


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
    url(r'^taxaInvestigator$', 'MiRA.views.taxaInvestigator.getRareTaxa', name='taxaInvestigator'),
    url(r'^attributes', 'MiRA.views.attributes.main', name='attributes'),
    url(r'^16sProfileBoxplot', 'MiRA.views.16sProfileBoxplot.main', name='16sProfileBoxplot'),
    url(r'^stackedbars', 'MiRA.views.stackedbars.main', name='stackedbars'),
    url(r'^clustering', 'MiRA.views.clustering.manager', name='clustering'),
    url(r'^heatmap', 'MiRA.views.heatmap.manager', name='heatmap'),
    url(r'^area', 'MiRA.views.area.main', name='area'),
    url(r'^analytics', 'MiRA.views.analytics.main', name='analytics'),
    url(r'^createProject', 'MiRA.views.createProject.main', name='createProject'), 
    url(r'^joinProject/(?P<invitecode>\w{40})', 'MiRA.views.joinProject.main', name='joinProject'), 
    url(r'^project/(?P<invitecode>\w{40})', 'MiRA.views.projectPage.main', name='projectPage'), 
    url(r'^diversity/alpha2', 'MiRA.views.diversity.alpha2', name='alpha2'),
    url(r'^diversity/alpha', 'MiRA.views.diversity.alpha', name='alpha'),
    url(r'^diversity/beta', 'MiRA.views.diversity.beta', name='beta'),
    url(r'^pca$', 'MiRA.views.pca.main', name='pca'),
    url(r'^lefse2', 'MiRA.views.lefse2.main', name='lefse2'),
    url(r'^lefse', 'MiRA.views.lefse.main', name='lefse'),
    url(r'^query/build', 'MiRA.views.buildquery.main', name='buildquery'),
    url(r'^query/merge', 'MiRA.views.buildquery.merge', name='mergequery'),
    url(r'^query/dataset', 'MiRA.views.buildquery.dataset', name='datasetquery'),
    url(r'^query/samplebased', 'MiRA.views.samplebasedquery.main', name='samplebasedquery'),
    url(r'^query/manage', 'MiRA.views.managequeries.main', name='managequeries'),
    url(r'^chooseproject', 'MiRA.views.chooseproject.main', name='chooseproject'),
    url(r'^manageProject', 'MiRA.views.manageProject.main', name='manageProject'), 
    url(r'^publicProjects', 'MiRA.views.publicProjects.enroll', name='publicProjects'), 
    url(r'^login', 'MiRA.views.login.main', name='login'),
    url(r'^logout', 'MiRA.views.logout.main', name='logout'),
    url(r'^registerNewUser', 'MiRA.views.registerNewUser.main', name='registerNewUser'),
    url(r'^activateNewUser/(?P<token>\w{32})/$', 'MiRA.views.activateNewUser.main', name='activateNewUser'),
    url(r'requestPasswordReset', 'MiRA.views.resetPassword.requestReset', name='requestReset'),
    url(r'resetPassword/(?P<token>\w{32})/$', 'MiRA.views.resetPassword.main', name='resetPassword'),
    url(r'timecourse/table', 'MiRA.views.timecourse.viewTimecourseInTable', name='timecourseTable'),

    # sample report urls
    url(r'sample/report', 'MiRA.views.samplereport.main', name='samplereport'),
    url(r'sample/fetch', 'MiRA.views.samplereport.fetchdata', name='fetchsampledata'),
    url(r'sample/krona', 'MiRA.views.samplereport.krona', name='krona'),

    # file upload
    url(r'upload/taxa', 'api.uploads.taxa.main', name='uploadTaxa'),
    url(r'upload/analysis', 'api.uploads.analysis.main', name='uploadAnalysis'),
    url(r'upload/metadata', 'api.uploads.metadata.main', name='uploadMetadata'),
    url(r'upload/status', 'api.uploads.status.main', name='uploadStatus'),

    # documentation
    url(r'^documentation$', TemplateView.as_view(template_name='documentation.html'), name='documentation'),

)
