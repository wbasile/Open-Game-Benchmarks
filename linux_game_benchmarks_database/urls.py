from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

import lgbdb.views


urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^$', lgbdb.views.home, name='home'),
    url(r'^about/$', lgbdb.views.about, name='about'),
    
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/profile/$', lgbdb.views.profile, name='profile'),
    
    url(r'^system_add/$', lgbdb.views.SystemAddEditView, name='add_system'),
    url(r'^system_edit/(?P<pk>\d+)$', lgbdb.views.SystemAddEditView, name='edit_system'),
    url(r'^system_delete/(?P<pk>\d+)$', lgbdb.views.SystemDeleteView.as_view(), name='system-delete',),
    
    url(r'^benchmark_add/$', lgbdb.views.BenchmarkAddEditView, name='benchmark-add'),
    url(r'^benchmark_edit/(?P<pk>\d+)$', lgbdb.views.BenchmarkAddEditView, name='benchmark-edit'),
    url(r'^benchmark_detail/(?P<pk>\d+)$', lgbdb.views.BenchmarkDetailView.as_view(), name='benchmark-detail',),
    url(r'^benchmark_delete/(?P<pk>\d+)$', lgbdb.views.BenchmarkDeleteView.as_view(), name='benchmark-delete',),
        
    url(r'^benchmark_table/$', lgbdb.views.BenchmarkTableView.as_view(), name='benchmark-table'),
    url(r'^benchmark_chart/$', lgbdb.views.fps_chart_view, name='benchmark-chart'),
    
    url(r'^game_list/$', lgbdb.views.GameListView.as_view(), name='game-list'),
    
]
