
from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponseForbidden
from .forms import SystemAddEditForm, BenchmarkAddForm, BenchmarkEditForm
from .models import System,Benchmark, Game, NewsPost
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.generic import DeleteView
from django.views.generic import DetailView, TemplateView
from django.core.urlresolvers import reverse

from django import forms

from django.db.models import Count

import django_tables2 as tables
from django_tables2   import RequestConfig
from django.utils.safestring import mark_safe
from django.utils.html import escape


import django_filters

from graphos.sources.simple import SimpleDataSource
from graphos.sources.model import ModelDataSource
from graphos.renderers import gchart, flot



# the home page / landing page
# it contains a list of the latest benchmarks, a news panel and a statistics panel
def home(request):
    
    
    # compute some statistics; TODO: add more!
    num_users = User.objects.count()
    num_games = Game.objects.count()
    num_benchmarks = Benchmark.objects.count()
    
    # compute the highest-fps benchmark
    if Benchmark.objects.count() > 0:
        best_fps_benchmark = Benchmark.objects.order_by("-fps_avg")[0]
    else:
        best_fps_benchmark = None
    
        
    # compute the most popular game
    if Game.objects.count() > 0 and Benchmark.objects.count() > 0:
        most_popular_game = Game.objects.annotate(num_benchmarks=Count('benchmark')).order_by('-num_benchmarks')[0]
    else:
        most_popular_game = None
        
        
    # list of the most recently submitted 10 benchmarks
    if Benchmark.objects.count() > 0:
        recent_benchmarks = Benchmark.objects.all().order_by('-upload_date')[0:10]
    else:
        recent_benchmarks = []
        
        
    latest_post = NewsPost.objects.order_by('-posted')[0]
        
    context = {
        'num_users' : num_users,
        'num_games' : num_games,
        'num_benchmarks' : num_benchmarks,
        'best_benchmark' : best_fps_benchmark,
        'most_popular_game' : most_popular_game,
        'benchmarks_table' : recent_benchmarks,
        'latest_post':latest_post,
    }
    
    return render(request, "home.html", context)



# a simple help and about page; the entire thing is done in the template at the moment
def about(request):
    return render(request, "about.html", {})
        
    
# a page to display when the user tries to see benchmarks for a game that does not have any
def GameNoBenchmark(request):
    return render(request, "no_benchmark.html", {})



# create a simple filter for Games
class GameFilter(django_filters.FilterSet):

    # free text search
    # TODO: implement autocomplete/typing suggestions
    title = django_filters.CharFilter(lookup_type='icontains')
    
    # a field to choose which subset of games we will display
    SHOW_CHOICES = (
                    (0, 'Show all games'),
                    (1, 'Show games with benchmarks'),
                    (2, 'Show games without benchmarks'),
                    )
    
    show = django_filters.MethodFilter(action="my_custom_filter",widget=forms.Select(choices=SHOW_CHOICES))

    
    class Meta:
        model = Game
        
        # these fields work even if the relative fields are hidden (excluded in the table)
        fields = ["title", "show"]
        
    
    # a function called by the "show" filter field, to generate a queryset based on a  given value    
    def my_custom_filter(self, queryset, value):
        
        if value == "1":
            return queryset.annotate(num_benchmarks=Count('benchmark')).filter(num_benchmarks__gt=0)
        elif value == "2":
            return queryset.annotate(num_benchmarks=Count('benchmark')).filter(num_benchmarks=0)
        else:
            return queryset




# a django-tables2 table, used in the Game List Page
class GameTable(tables.Table):
    
    # two custom columns, with values computed on the fly (server-side)
    num_benchmarks = tables.Column(verbose_name="Num benchmarks",empty_values=(), orderable=True)
    steamdb_link = tables.Column(verbose_name="",empty_values=(), orderable=False)
    
    class Meta:
        model = Game
        fields = ("title", "steam_appid","num_benchmarks")

    
    def render_num_benchmarks(self,record):
   
        value = int(record.benchmark_set.count())
        
        if value > 0:
            return mark_safe('<a href="/benchmark_table/?game=' + str(record.id) + '" >' + str(value) + '</a>')
        else:
            return str(value)

    
    # for the game title column, display a thumbnail of the game, and make it link to the Benchmark Table Page (filtered for that game)
    def render_title(self,record):
        img_url = "https://steamcdn-a.akamaihd.net/steam/apps/"+str(record.steam_appid)+"/capsule_sm_120.jpg"
        
        value = int(record.benchmark_set.count())
        
        if value > 0:
            return mark_safe('<a href="/benchmark_table/?game=' + str(record.id) + '" >' + '<img src="%s" />' % escape(img_url) + " " + unicode(record.title)+"</a>")
        else:
            return mark_safe('<a href="/no_benchmark">' + '<img src="%s" />' % escape(img_url) + " " + unicode(record.title)+"</a>")
            
            
    # a simple link to steamdb.info
    def render_steamdb_link(self, record):
        value = record.steam_appid
        
        return mark_safe('<a target="_blank" class="btn btn-xs btn-danger" href="http://steamdb.info/app/' + str(value) + '/" >SteamDB</a>')
        
        

# a view that combines table and filters
class GameListView(TemplateView):
    
    template_name = 'game_list.html'

    def get_queryset(self, **kwargs):
        return Game.objects.all()

    def get_context_data(self, **kwargs):
        context = super(GameListView, self).get_context_data(**kwargs)
        filter = GameFilter(self.request.GET, queryset=self.get_queryset(**kwargs))
        
        filter.form.fields['title'].widget.attrs = {'placeholder': "Search by title",}
        filter.form.fields['title'].label = "Search"
        filter.form.fields['title'].help_text = ""
        
        filter.form.fields['show'].label = "Display options"
        filter.form.fields['show'].help_text = ""
        
        
        # intercept the case in which we are trying to sort by num_benchmarks, which is not a field of the Game model (so it would give an error)
        if self.request.GET.get('sort',None) == "num_benchmarks":
            
            # remove the "sort by num benchmarks" in the GET dictionary
            nr = self.request.GET.copy()
            arg = nr.pop("sort")[0]
            self.request.GET = nr

            #  modify the filtered queryset by sorting it manually, using the annotate function 
            new_qs = filter.qs.annotate(num_benchmarks=Count('benchmark')).order_by('-num_benchmarks')
            table = GameTable(new_qs)
            
        else:
            table = GameTable(filter.qs)
            
        RequestConfig(self.request).configure(table)
            
        context['filter'] = filter
        context['table'] = table
        
        return context
        
        
        
        
        

# create a filter for Benchmarks
class BenchmarkFilter(django_filters.FilterSet):

    class Meta:
        model = Benchmark
        
        # these fields work even if the relative fields are hidden (excluded in the table)
        fields = ["game","cpu_model","gpu_model","resolution", "driver","operating_system"]
        
        # this doesn't work :(
        #~ fields = ['user_system.cpu_model']
        
    def __init__(self, *args, **kwargs):
        super(BenchmarkFilter, self).__init__(*args, **kwargs)

        # limit the possible choices in the filter to the items that are in the benchmark list, plus an "any" choice
        # for example, limit the choices in "Game" only to the game that have at least one benchmark
        
        ANY_CHOICE = ('', '---------'),
            
        for field_name in BenchmarkFilter.Meta.fields:
            # limit the multiple choice for the MultipleChoice (text) fields 
            if 'choices' in self.filters[field_name].extra.keys():
                choice_set = sorted(set([i[0] for i in Benchmark.objects.values_list(field_name)]))
                self.filters[field_name].extra['choices'] = ANY_CHOICE + tuple(zip(choice_set,choice_set))
        
            # setting the multiple choice for Games is a bit more complicated, because it's a Foreign key
            elif 'queryset' in self.filters[field_name].extra.keys() and field_name == 'game':
                query_id_set = set([i[0] for i in Benchmark.objects.values_list(field_name)])
                self.filters[field_name].extra['queryset'] = Game.objects.filter(pk__in=query_id_set)
                
        # correct capitalization in the labels
        self.filters['cpu_model'].label = "CPU Model"        
        self.filters['gpu_model'].label = "GPU Model"        


        
# a django-tables2 table, used in the Benchmark Table Page
class BenchmarkTable(tables.Table):
    
    # two custom columns: a button that links to that benchmark detail page, and the Interquartile Range
    benchmark_detail = tables.Column(verbose_name="",empty_values=(), orderable=False)
    IQR = tables.Column(verbose_name="IQR",empty_values=(), orderable=False)


    class Meta:
        model = Benchmark
        fields = ("game", "cpu_model", "gpu_model", "resolution","game_quality_preset","fps_median","IQR", "operating_system","additional_notes", "user")
    
    
    def __init__(self, *args, **kwargs):
        super(BenchmarkTable, self).__init__(*args, **kwargs)
    
        # correct capitalization of acronyms
        self.base_columns['cpu_model'].verbose_name = "CPU Model"
        self.base_columns['gpu_model'].verbose_name = "GPU Model"
    
        # TODO: move here the formatting of IQR heading (with the info popover); now it is a hack in the template
    
    
    # image thumbnail in the game field
    def render_game(self, value):
        img_url = "https://steamcdn-a.akamaihd.net/steam/apps/"+str(value.steam_appid)+"/capsule_sm_120.jpg"
        return mark_safe('<a href="/benchmark_table/?game=' + str(value.pk) + '" >' + '<img src="%s" /><br>' % escape(img_url) + " " + unicode(value.title)+"</a>")
        

    def render_benchmark_detail(self, record):
        button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="btn btn-sm btn-warning">Detail</a>'
        return mark_safe(button_html)
        
        
    def render_IQR(self, record,column):
        iqr_value = record.fps_3rd_quartile - record.fps_1st_quartile
        return mark_safe(str(iqr_value))
        
        
    def render_additional_notes(self,value):
        return mark_safe('''<a href="#" class="btn btn-xs btn-default" data-toggle="popover"  data-trigger="hover" title="Notes" data-content="'''+unicode(value)+'''">View notes</a>''')

    
    # different font color for linux and windows
    #~ def render_operating_system(self,value):
        #~ print value
        #~ if value.find("Windows") != -1:
            #~ return mark_safe('<font color="blue">'+unicode(value)+'</font>')
        #~ else:
            #~ return mark_safe('<font color="red">'+unicode(value)+'</font>')



# a view that combines table and filter
class BenchmarkTableView(TemplateView):
    
    template_name = 'benchmark_table.html'

    def get_queryset(self, **kwargs):
        return Benchmark.objects.order_by("upload_date").reverse()

    def get_context_data(self, **kwargs):
        context = super(BenchmarkTableView, self).get_context_data(**kwargs)
        filter = BenchmarkFilter(self.request.GET, queryset=self.get_queryset(**kwargs))
        
        for f in filter.form.fields:
            filter.form.fields[f].help_text = ""
             
        table = BenchmarkTable(filter.qs)
        RequestConfig(self.request).configure(table)
        
        context['filter'] = filter
        context['table'] = table
        context['infotext'] = str(len(filter.qs)) + " benchmark(s) found with these criteria"
        
        return context
        
        
        
        

# this function builds the label of each bar 
def set_benchmark_y_label(benchmark):
    
    if benchmark.game_quality_preset != "n.a.":
        #~ y_tick_label = "<br>".join([str(x) for x in [str(benchmark.game) + " - " + benchmark.game_quality_preset + " preset, at: " + benchmark.resolution, benchmark.cpu_model + " " + benchmark.gpu_model, benchmark.operating_system ] ])
        
        first_line = " ".join([str(x) for x in [benchmark.game,benchmark.game_quality_preset + " preset, at: " + benchmark.resolution]])
        
        y_tick_label = "<br>".join([str(x) for x in [first_line, benchmark.cpu_model + " " + benchmark.gpu_model, benchmark.operating_system ] ])
    else:
        #~ y_tick_label = "<br>".join([str(x) for x in [str(benchmark.game) + " - " + " at: " + benchmark.resolution, benchmark.cpu_model + " " + benchmark.gpu_model, benchmark.operating_system ] ])
        first_line = " ".join([str(x) for x in [benchmark.game, "at: " + benchmark.resolution]])
        y_tick_label = "<br>".join([str(x) for x in [first_line, benchmark.cpu_model + " " + benchmark.gpu_model, benchmark.operating_system ] ])
        
    return str(y_tick_label)

    

# bar plot with multiple benchmarks using graphos and flot
def fps_chart_view(request):
    
    max_displayed_benchmarks = 30
    
    f = BenchmarkFilter(request.GET, queryset=Benchmark.objects.order_by("upload_date").reverse())
    
    queryset = queryset = Benchmark.objects.filter(pk__in=[x.pk for x in f[0:min([len(f), max_displayed_benchmarks])]]).order_by("fps_median")

    
    data = [["","Median FPS"]]
    
    yticks = []    
        
    for s,q in enumerate(queryset):
        #~ iqr = q.fps_3rd_quartile-q.fps_1st_quartile
        data += [[q.fps_median,s+1 ]]
        yticks += [[s+1,set_benchmark_y_label(q)]]
        
    data_source = SimpleDataSource(data=data)
        
    options_dic = {
                    'legend': {'show': False},
                    'bars' : {'barWidth':0.3,"horizontal":True,"align":"center"},
                    "grid":{"hoverable":True},
                    
                    "yaxis":{
                            "ticks":yticks,
                            },
                    }
                    
    height = len(queryset) * 60
    
    chart = flot.BarChart(data_source,height=height, options=options_dic)
    
    return render(request, "benchmark_chart.html", {'max_bench_num':max_displayed_benchmarks,'filter': f, 'chart': chart})


# benchmark fps line plot using graphos and flot
def fps_line_chart(benchmark):
    
    if not benchmark: return None
    
    data =  [['Second', 'FPS','Median','1st Quartile','3rd Quartile']]
        
    for s,f in enumerate(benchmark.fps_data.split(",")):
        data += [[int(s),int(f), int(benchmark.fps_median), int(benchmark.fps_1st_quartile), int(benchmark.fps_3rd_quartile)]]
        
    data_source = SimpleDataSource(data=data)
        
    chart = flot.LineChart(data_source, options={'title': "Frames per second"})
        
    return chart    
    
    

# a simple view to display the benchmark fps line graph and all the info of the given benchmark
def BenchmarkDetailView(request, pk=None):
    
    benchmark = get_object_or_404(Benchmark, pk=pk)
    
    if benchmark:

        chart = fps_line_chart(benchmark)
        return render(request, "benchmark_detail.html", {'object':benchmark,'fpschart': chart})



# user profile page
@login_required
def profile(request):

    uss = request.user.system_set.all()
    usb = request.user.benchmark_set.order_by("upload_date").reverse()
           
    context = { "uss":uss, "benchmarks_table":usb}
    
    return render(request, 'profile.html', context)
    
    
    
# page with form to add or edit systems
@login_required    
def SystemAddEditView(request, pk=None):
    
    if pk:  # this means that we are trying to edit an existing instance
        system = get_object_or_404(System, pk=pk) # try to get the instance
        if system.user != request.user: # check if the instance belongs to the requesting user
            return HttpResponseForbidden()
    
    else:
        system = None  

    
    
    if request.method == 'POST':
        form = SystemAddEditForm(request.POST,user=request.user, instance=system)
        if form.is_valid():
            
            # get the data
            instance = form.save(commit=False)
            
            # Do something with the data
            # ensure that the owner of this system is the current user
            instance.user = request.user

            # save the data
            # instance is an instance of System
            instance.save()
                
            return HttpResponseRedirect('/accounts/profile')
    else:
        form = SystemAddEditForm(user=request.user,initial={'user': request.user}, instance=system)    
        
    
    if system:    
        title = 'Edit system "' + str(system) + '"'
    else:
        title = "Add new system"
             
    context = {"form":form , "title":title}
    
    return render(request, "system_add_edit.html",context)
    


# page to delete a system
class SystemDeleteView(DeleteView):
    
    def dispatch(self, *args, **kwargs):
        
        # verify that the object exists
        system = get_object_or_404(System, pk=kwargs['pk'])
        
        # check that the user tryng to delete the system is the owner of that system 
        # (this prevents also anonymous, non-logged-in users to delete)
        if system.user == self.request.user:  
            return super(SystemDeleteView, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseForbidden("Forbidden")
            
    
    model = System
    template_name = 'system_delete.html'

    def get_success_url(self):
        return reverse('profile')
        
        
        
            
# page with form to add or add a benchmark
@login_required    
def BenchmarkAddView(request):
    
    if request.method == 'POST':
        
        form = BenchmarkAddForm(request.POST, request.FILES,user=request.user)
        
        if form.is_valid():
            
            # ensure that the owner of this system is the current user
            # I don't think this is really needed
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            return HttpResponseRedirect('/accounts/profile/')
            
    else:
        form = BenchmarkAddForm(user=request.user,initial={'user': request.user})
            
    
    title = "Add new benchmark"
    
    context = {"form":form , "title":title}
    
    template = "benchmark_add.html"
    
    return render(request, template ,context)
    

    

# page with form to add or edit benchmarks
# it also contains the fps graph 
@login_required    
def BenchmarkEditView(request, pk=None):
    
    benchmark = get_object_or_404(Benchmark, pk=pk) # try to get the instance
    if benchmark.user != request.user: # check if the instance belongs to the requesting user
        return HttpResponseForbidden("Forbidden")


    if request.method == 'POST':
        
        form = BenchmarkEditForm(request.POST, request.FILES, instance=benchmark)
            
        if form.is_valid():
            # ensure that the owner of this system is the current user
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
                
            return HttpResponseRedirect('/accounts/profile/')

    else:
        form = BenchmarkEditForm(instance=benchmark)
            
            
    title = 'Edit benchmark "' + str(benchmark) + '"'
    
    chart = fps_line_chart(benchmark)

    context = {"form":form , "title":title, "fpschart":chart}
    
    template = "benchmark_edit.html"
        
    return render(request, template ,context)        
            
            
            
            
            
# page to delete a benchmark
class BenchmarkDeleteView(DeleteView):
    
    def dispatch(self, *args, **kwargs):
        
        # verify that the object exists
        benchmark = get_object_or_404(Benchmark, pk=kwargs['pk'])
        
        # check that the user tryng to delete the system is the owner of that system 
        # (this prevents also anonymous, non-logged-in users to delete)
        if benchmark.user == self.request.user:  
            self.game = benchmark.game
            return super(BenchmarkDeleteView, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseForbidden("Forbidden")
            
    
    model = Benchmark
    template_name = 'benchmark_delete.html'

    def get_success_url(self):
        
        return reverse('profile')
        
        


    
