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
    url(r'^accounts/profile/$', lgbdb.views.user_profile, name='user-profile-default'),
    url(r'^accounts/profile/(?P<pk>\d+)$', lgbdb.views.user_profile, name='user-profile'),
    
    url(r'^system_detail/(?P<pk>\d+)$', lgbdb.views.SystemDetailView, name='system-detail',),
    url(r'^system_add/$', lgbdb.views.SystemAddEditView, name='system-add'),
    url(r'^system_edit/(?P<pk>\d+)$', lgbdb.views.SystemAddEditView, name='system-edit'),
    url(r'^system_delete/(?P<pk>\d+)$', lgbdb.views.SystemDeleteView, name='system-delete',),
    
    url(r'^benchmark_detail/(?P<pk>\d+)$', lgbdb.views.BenchmarkDetailView, name='benchmark-detail',),
    url(r'^benchmark_add/$', lgbdb.views.BenchmarkAddView, name='benchmark-add'),
    url(r'^benchmark_edit/(?P<pk>\d+)$', lgbdb.views.BenchmarkEditView, name='benchmark-edit'),
    url(r'^benchmark_delete/(?P<pk>\d+)$', lgbdb.views.BenchmarkDeleteView, name='benchmark-delete',),
        
    url(r'^benchmark_table/$', lgbdb.views.BenchmarkTableView, name='benchmark-table'),
    url(r'^benchmark_chart/$', lgbdb.views.BenchmarkChartView, name='benchmark-chart'),
    url(r'^no_benchmark/$', lgbdb.views.GameNoBenchmark, name='no-benchmark'),
    
    url(r'^game_table/$', lgbdb.views.GameTableView, name='game-table'),
    
    url(r'^benchmark_rss/', lgbdb.feeds.LatestBenchmarks()),
    
    url(r'^forums/', include('simple_forums.urls')),
    
]
