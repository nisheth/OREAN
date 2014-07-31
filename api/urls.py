from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User, Group
from rest_framework import routers
from . import views

#router = routers.DefaultRouter()
#router.register(r'analysis', views.AnalysisViewSet, 'Analysis')
#router.register(r'listprojects', views.ProjectViewSet, 'Project')
#router.register(r'listdatasets', views.DataSetView.as_View(), 'Dataset')

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.APIRoot.as_view(), name='APIRoot'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^ListDatasets/$', views.ListDatasets.as_view(), name='ListDatasets'),
    url(r'^ListProjects/$', views.ListProjects.as_view(), name='ListProjects'),
    url(r'^ListMethods/$', views.ListMethods.as_view(), name='ListMethods'),
    url(r'^ListCategories/$', views.ListCategories.as_view(), name='ListCategories'),
    url(r'^ListAttributes/$', views.ListAttributes.as_view(), name='ListAttributes'),
    url(r'^BuildQuery/$', views.BuildQuery.as_view(), name='BuildQuery'),
    url(r'^ShowDistribution/$', views.ShowDistribution.as_view(), name='ShowDistribution'),
    url(r'^ListQueries/$', views.ListQueries.as_view(), name='ListQueries'),
    url(r'^GetData/$', views.GetData.as_view(), name='GetData'),
    url(r'^GetDataset/$', views.GetDataset.as_view(), name='GetDataset'),
    url(r'^MergeQuery/$', views.MergeQuery.as_view(), name='MergeQuery'),
    url(r'^BuildDatasetQuery/$', views.BuildDatasetQuery.as_view(), name='BuildDatasetQuery'),
    url(r'^DeleteQuery/$', views.DeleteQuery.as_view(), name='DeleteQuery'),
    url(r'^ShareQuery/$', views.ShareQuery.as_view(), name='ShareQuery'),
    url(r'^ListTaxa/$', views.ListTaxa.as_view(), name='ListTaxa'),
)
