
from .forms import SystemAddEditForm, BenchmarkAddForm, BenchmarkEditForm
from .models import System,Benchmark, Game, NewsPost
from .filters import GameFilter, BenchmarkFilter
from .tables import GameTable, BenchmarkTable, BenchmarkChartTable
from django_tables2   import RequestConfig


from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.template import RequestContext

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
        benchmark_table = BenchmarkTable(recent_benchmarks,user=request.user)
        RequestConfig(request).configure(benchmark_table)
        
        # exclude some fields from this table since it is used in the home page
        benchmark_table.exclude = ["IQR","additional_notes"]
        
        # make it not sortable, because we are using a sliced queryset
        benchmark_table._orderable = False
        
        # disable pagination
        benchmark_table.page = None
        
    else:
        benchmark_table = None
        
    latest_post = NewsPost.objects.order_by('-posted')[0]
        
    context = {
        'num_users' : num_users,
        'num_games' : num_games,
        'num_benchmarks' : num_benchmarks,
        'best_benchmark' : best_fps_benchmark,
        'most_popular_game' : most_popular_game,
        'benchmark_table' : benchmark_table,
        'latest_post':latest_post,
    }
    
    return render(request, "home.html", context)




# user profile page
def user_profile(request,pk=None):
    
    # if the pk of the user to view is not provided, try to display the profile of the currently logged user

    if not pk:
        if request.user.is_authenticated():
            pk = request.user.pk
        
    user = get_object_or_404(User, pk=pk)
        
    uss = user.system_set.all()    
    
    #~ system_table = SystemTable(uss)
    #~ RequestConfig(request).configure(system_table)
    
    usb = user.benchmark_set.order_by("upload_date").reverse()
    benchmark_table = BenchmarkTable(usb,user=request.user)
    RequestConfig(request).configure(benchmark_table)
    benchmark_table.exclude = ["user"]
    
    context = { "uss":uss,"usb":usb, "benchmark_table":benchmark_table, "userobject":user}
    
    return render(request, 'user_profile.html', context)
    
    
    
    

# a simple help and about page; the entire thing is done in the template at the moment
def about(request):
    return render(request, "about.html", {})
        
    
# a page to display when the user tries to see benchmarks for a game that does not have any
def GameNoBenchmark(request):
    return render(request, "no_benchmark.html", {})





def GameTableView(request):
    
    filter = GameFilter(request.GET)
    filter.form.fields['title'].widget.attrs = {'placeholder': "Search by title",}
    filter.form.fields['title'].label = "Game Title"
    filter.form.fields['title'].help_text = ""
    filter.form.fields["title"].widget.attrs["list"] = "mylist" # <- list needed to autocomplete
    gamelist = Game.objects.all()
    
    filter.form.fields['show'].label = "Display options"
    filter.form.fields['show'].help_text = ""
    
    # little hack to make the django_table2 sortable by a field with a computed value    
    # intercept the case in which we are trying to sort by num_benchmarks, which is not a field of the Game model (so it would give an error)
    if request.GET.get('sort',None) == "num_benchmarks":
        
        # remove the "sort by num benchmarks" in the GET dictionary
        nr = request.GET.copy()
        arg = nr.pop("sort")[0]
        request.GET = nr

        #  modify the filtered queryset by sorting it manually, using the annotate function 
        new_qs = filter.qs.annotate(num_benchmarks=Count('benchmark')).order_by('-num_benchmarks')
        table = GameTable(new_qs)
        
    else:
        table = GameTable(filter.qs)
                            
    RequestConfig(request).configure(table)
        
    context = {
        'filter' : filter,
        'table' : table,
        "gamelist" : gamelist,
    }
    
    return render(request, "game_table_view.html", context)
    
    



def BenchmarkTableView(request):
    
    if "btn-other" in request.GET:
        add_get = "&".join([x+"="+request.GET[x] for x in request.GET.keys() if x != "btn-other"])
        return HttpResponseRedirect('/benchmark_chart/?'+add_get)
        
    filter = BenchmarkFilter(request.GET)
        
    for f in filter.form.fields:
        filter.form.fields[f].help_text = ""
    
    filter.form.fields['game'].widget.attrs = {'placeholder': "Search by title",}
    filter.form.fields['game'].label = "Game Title"
    filter.form.fields["game"].widget.attrs["list"] = "mylist" # <- list needed to autocomplete
    
    query_id_set = set([i[0] for i in Benchmark.objects.values_list("game")])
    gamelist = Game.objects.filter(pk__in=query_id_set)
   
    table = BenchmarkTable(filter.qs.order_by("-upload_date"),user=request.user)
    RequestConfig(request).configure(table)
        
    context = {
        'filter' : filter,
        'table' : table,
        'gamelist' : gamelist
    }
    
    return render(request, "benchmark_table_view.html", context)
    
    


def BenchmarkChartView(request):
    
    if "btn-other" in request.GET:
        add_get = "&".join([x+"="+request.GET[x] for x in request.GET.keys() if x != "btn-other"])
        return HttpResponseRedirect('/benchmark_table/?'+add_get)
        
    filter = BenchmarkFilter(request.GET)
        
    for f in filter.form.fields:
        filter.form.fields[f].help_text = ""
             
    table = BenchmarkChartTable(filter.qs.order_by("-upload_date"))
    RequestConfig(request).configure(table)
        
    context = {
        'filter' : filter,
        'table' : table,
        'chart' : True
    }
    
    return render(request, "benchmark_chart_view.html", context)
    
      


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
def SystemDetailView(request, pk=None):
    
    system = get_object_or_404(System, pk=pk)
    
    form = SystemAddEditForm(instance=system)    
    
    action = "detail"
    
    return render(request, "system_action.html", {'object':system, 'action':action, 'form':form})
    
    
    
    
# page with form to add or edit systems
@login_required    
def SystemAddEditView(request, pk=None):
    
    if pk:  # this means that we are trying to edit an existing instance
        system = get_object_or_404(System, pk=pk) # try to get the instance
        if system.user != request.user: # check if the instance belongs to the requesting user
            return HttpResponseForbidden()
        else:
            action = "edit"
    else:
        system = None  
        action = "add"

    
    
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
                
            return HttpResponseRedirect('/accounts/profile/'+str(request.user.pk))
    else:
        form = SystemAddEditForm(user=request.user,initial={'user': request.user}, instance=system)    
        
             
    context = {'object':system, "form":form , "action":action}
    
    return render(request, "system_action.html",context)
    




# page to delete a system
def SystemDeleteView(request, pk=None):
    
    system = get_object_or_404(System, pk=pk)
    
    # check that the user tryng to delete the system is the owner of that system 
    # (this prevents also anonymous, non-logged-in users to delete)
    if system.user != request.user:  
        return HttpResponseForbidden("Forbidden")
        
    if request.method == "POST":
        system.delete()
        return HttpResponseRedirect('/accounts/profile/'+str(request.user.pk))
        
        
    form = SystemAddEditForm(user=request.user,initial={'user': request.user}, instance=system)    
    
    action = "delete"
    
    return render(request, "system_action.html", {'object':system, 'action':action, 'form':form})
    
    


# a simple view to display the benchmark fps line graph and all the info of the given benchmark
def BenchmarkDetailView(request, pk=None):
    
    benchmark = get_object_or_404(Benchmark, pk=pk)
    
    chart = fps_line_chart(benchmark)
    
    form = BenchmarkEditForm(instance=benchmark)   
    
    iqr =  benchmark.fps_3rd_quartile - benchmark.fps_1st_quartile
    
    action = "detail"
    
    return render(request, "benchmark_action.html", {'object':benchmark,'fpschart': chart, 'action':action, 'form':form, 'iqr':iqr})

        
        
        
        
            
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

            return HttpResponseRedirect('/accounts/profile/'+str(request.user.pk))
            
    else:
        form = BenchmarkAddForm(user=request.user,initial={'user': request.user})
            

    
    action = "add"
    
    context = {'object':None, "form":form , "action":action}
    
    template = "benchmark_action.html"
    
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
                
            return HttpResponseRedirect('/accounts/profile/'+str(request.user.pk))

    else:
        form = BenchmarkEditForm(instance=benchmark)
            
                
    chart = fps_line_chart(benchmark)
    
    action = "edit"
    
    context = {'object':benchmark, "form":form , "action":action, "fpschart":chart}
    
    template = "benchmark_action.html"
        
    return render(request, template ,context)        
            
            
            
            
# page to delete a system
def BenchmarkDeleteView(request, pk=None):
    
    benchmark = get_object_or_404(Benchmark, pk=pk)
    
    # check that the user tryng to delete the system is the owner of that system 
    # (this prevents also anonymous, non-logged-in users to delete)
    if benchmark.user != request.user:  
        return HttpResponseForbidden("Forbidden")
        
    if request.method == "POST":
        benchmark.delete()
        return HttpResponseRedirect('/accounts/profile/'+str(request.user.pk))
        
    
    chart = fps_line_chart(benchmark)
    
    form = BenchmarkEditForm(instance=benchmark)    
    
    action = "delete"
    
    iqr =  benchmark.fps_3rd_quartile - benchmark.fps_1st_quartile
    
    return render(request, "benchmark_action.html", {'object':benchmark, 'action':action, 'form':form,'fpschart':chart, 'iqr':iqr})


            
# page to delete a benchmark
#~ class BenchmarkDeleteView(DeleteView):
    #~ 
    #~ def dispatch(self, *args, **kwargs):
        #~ 
        #~ # verify that the object exists
        #~ benchmark = get_object_or_404(Benchmark, pk=kwargs['pk'])
        #~ 
        #~ # check that the user tryng to delete the system is the owner of that system 
        #~ # (this prevents also anonymous, non-logged-in users to delete)
        #~ if benchmark.user == self.request.user:  
            #~ self.game = benchmark.game
            #~ return super(BenchmarkDeleteView, self).dispatch(*args, **kwargs)
        #~ else:
            #~ return HttpResponseForbidden("Forbidden")
            #~ 
    #~ 
    #~ model = Benchmark
    #~ template_name = 'benchmark_delete.html'
#~ 
    #~ def get_success_url(self):
        #~ 
        #~ return reverse('profile')
        #~ 
        #~ 
#~ 
#~ 
    #~ 
