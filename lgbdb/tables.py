from .models import Benchmark, Game
import django_tables2 as tables

from django.utils.safestring import mark_safe
from django.utils.html import escape




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
        
        
        


# a django-tables2 table, used in the Benchmark Table Page
class BenchmarkTable(tables.Table):
    
    # two custom columns: a button that links to that benchmark detail page, and the Interquartile Range
    benchmark_detail = tables.Column(verbose_name="",empty_values=(), orderable=False)
    IQR = tables.Column(verbose_name="IQR",empty_values=(), orderable=False)


    class Meta:
        model = Benchmark
        fields = ("game", "cpu_model", "gpu_model", "resolution","game_quality_preset","fps_median","IQR", "operating_system","additional_notes", "user")
    
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(BenchmarkTable, self).__init__(*args, **kwargs)
        
        # correct capitalization of acronyms
        self.base_columns['cpu_model'].verbose_name = "CPU"
        self.base_columns['gpu_model'].verbose_name = "GPU"
        self.base_columns['game_quality_preset'].verbose_name = "Settings"
        self.base_columns['additional_notes'].verbose_name = "Notes"
    
        # TODO: move here the formatting of IQR heading (with the info popover); now it is a hack in the template
    
    
    # image thumbnail in the game field
    def render_game(self, value):
        img_url = "https://steamcdn-a.akamaihd.net/steam/apps/"+str(value.steam_appid)+"/capsule_sm_120.jpg"
        return mark_safe('<a href="/benchmark_table/?game=' + str(value.pk) + '" >' + '<img src="%s" /><br>' % escape(img_url) + " " + unicode(value.title)+"</a>")
        

    def render_benchmark_detail(self, record):
        #display edit and delete buttons if the benchmark of this row belongs to the currently logged in user
        if self.user == record.user:
            
            button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="btn btn-xs btn-warning">Detail</a></td><td><a href="/benchmark_edit/' +str(record.id)+ '" class="btn btn-xs btn-info">Edit</a></td><td><a href="/benchmark_delete/' +str(record.id)+ '" class="btn btn-xs btn-danger">Delete</a>'
            
        else:
            button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="btn btn-xs btn-warning">Detail</a>'
            
        return mark_safe(button_html)
        
        
    def render_IQR(self, record,column):
        iqr_value = record.fps_3rd_quartile - record.fps_1st_quartile
        return mark_safe(str(iqr_value))
        
        
    def render_additional_notes(self,value):
        return mark_safe('''<a href="#" class="btn btn-xs btn-default" data-toggle="popover"  data-trigger="hover" title="Notes" data-content="'''+unicode(value)+'''">View notes</a>''')


    def render_user(self,value):
        return mark_safe('<a href="/accounts/profile/'+str(value.id)+'">'+str(value.username)+'</a>')

    # different font color for linux and windows
    #~ def render_operating_system(self,value):
        #~ print value
        #~ if value.find("Windows") != -1:
            #~ return mark_safe('<font color="blue">'+unicode(value)+'</font>')
        #~ else:
            #~ return mark_safe('<font color="red">'+unicode(value)+'</font>')


