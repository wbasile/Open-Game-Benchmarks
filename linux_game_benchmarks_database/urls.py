from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
admin.autodiscover()

import lgbdb.views
import lgbdb.feeds



urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^$', lgbdb.views.home, name='home'),
    url(r'^about/$', lgbdb.views.about, name='about'),
    
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}),

    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/profile/$', lgbdb.views.profile, name='profile'),
    
    url(r'^system_add/$', lgbdb.views.SystemAddEditView, name='add_system'),
    url(r'^system_edit/(?P<pk>\d+)$', lgbdb.views.SystemAddEditView, name='edit_system'),
    url(r'^system_delete/(?P<pk>\d+)$', lgbdb.views.SystemDeleteView.as_view(), name='system-delete',),
    
    url(r'^benchmark_add/$', lgbdb.views.BenchmarkAddView, name='benchmark-add'),
    url(r'^benchmark_edit/(?P<pk>\d+)$', lgbdb.views.BenchmarkEditView, name='benchmark-edit'),
    url(r'^benchmark_detail/(?P<pk>\d+)$', lgbdb.views.BenchmarkDetailView, name='benchmark-detail',),
    url(r'^benchmark_delete/(?P<pk>\d+)$', lgbdb.views.BenchmarkDeleteView.as_view(), name='benchmark-delete',),
        
    url(r'^benchmark_table/$', lgbdb.views.BenchmarkTableView.as_view(), name='benchmark-table'),
    url(r'^benchmark_chart/$', lgbdb.views.fps_chart_view, name='benchmark-chart'),
    
    url(r'^no_benchmark/$', lgbdb.views.GameNoBenchmark, name='no-benchmark'),
    
    url(r'^game_list/$', lgbdb.views.GameListView.as_view(), name='game-list'),
    
    url(r'^benchmark_rss/', lgbdb.feeds.LatestBenchmarks()),
    
]
