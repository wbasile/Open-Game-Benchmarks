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
            return mark_safe('<a href="/benchmark_table/?game=' + unicode(record.title) + '" >' + str(value) + '</a>')
        else:
            return unicode(value)

    
    # for the game title column, display a thumbnail of the game, and make it link to the Benchmark Table Page (filtered for that game)
    def render_title(self,record):
        img_url = "https://steamcdn-a.akamaihd.net/steam/apps/"+str(record.steam_appid)+"/capsule_sm_120.jpg"
        
        value = int(record.benchmark_set.count())
        
        if value > 0:
            return mark_safe('<a href="/benchmark_table/?game=' + unicode(record.title) + '" >' + '<img src="%s" />' % escape(img_url) + " " + unicode(record.title)+"</a>")
        else:
            return mark_safe('<a href="/no_benchmark">' + '<img src="%s" />' % escape(img_url) + " " + unicode(record.title)+"</a>")
            
            
    # a simple link to steamdb.info
    def render_steamdb_link(self, record):
        value = record.steam_appid
        
        return mark_safe('<a target="_blank" class="nounderline label label-primary" href="http://steamdb.info/app/' + unicode(value) + '/" >SteamDB</a>')
        
        
        


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
        img_url = "https://steamcdn-a.akamaihd.net/steam/apps/"+unicode(value.steam_appid)+"/capsule_sm_120.jpg"
        return mark_safe('<a href="/benchmark_table/?game=' + unicode(value.title) + '" >' + '<img src="%s" /><br>' % escape(img_url) + " " + unicode(value.title)+"</a>")
        

    def render_benchmark_detail(self, record):
        #display edit and delete buttons if the benchmark of this row belongs to the currently logged in user
        if self.user == record.user:
            
            #~ button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="btn btn-xs btn-warning">Detail</a></td><td><a href="/benchmark_edit/' +str(record.id)+ '" class="btn btn-xs btn-info">Edit</a></td><td><a href="/benchmark_delete/' +str(record.id)+ '" class="btn btn-xs btn-danger">Delete</a>'
            
            button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="nounderline label label-warning">Detail</a></td><td><a href="/benchmark_edit/' +str(record.id)+ '" class="nounderline label label-info">Edit</a></td><td><a href="/benchmark_delete/' +str(record.id)+ '" class="nounderline label label-danger">Delete</a>'
            
        else:
            button_html = '<a href="/benchmark_detail/' +str(record.id)+ '" class="nounderline label label-warning">Detail</a>'
            
        return mark_safe(button_html)
        
        
    def render_IQR(self, record,column):
        iqr_value = record.fps_3rd_quartile - record.fps_1st_quartile
        return mark_safe(str(iqr_value))
        
        
    def render_additional_notes(self,value):
        return mark_safe('''<a href="#" class="nounderline label label-default" data-toggle="popover"  data-trigger="hover" title="Notes" data-content="'''+unicode(value.replace('"','&quot;'))+'''">View notes</a>''')


    def render_user(self,value):
        return mark_safe('<a href="/accounts/profile/'+str(value.id)+'">'+unicode(value.username)+'</a>')


    def render_operating_system(self,value,record):
        
        if record.operating_system.lower().find("windows") != -1:
        
            return mark_safe('<a href="#" class="nounderline label label-primary" data-toggle="popover"  data-trigger="hover" title="OS" data-content="'+unicode(value)+'">'+value.split("(")[0]+'</a>')
        else:
            return mark_safe('<a href="#" class="nounderline label label-danger" data-toggle="popover" data-trigger="hover" title="OS" data-content="'+unicode(value)+'">'+value.split("(")[0]+'</a>')
            
            
        
    # different font color for linux and windows
    #~ def render_operating_system(self,value):
        #~ print value
        #~ if value.find("Windows") != -1:
            #~ return mark_safe('<font color="blue">'+unicode(value)+'</font>')
        #~ else:
            #~ return mark_safe('<font color="red">'+unicode(value)+'</font>')


# a django-tables2 table, used in the Benchmark Table Page
class BenchmarkChartTable(tables.Table):
    
    # this function builds the label of each bar 
    def set_benchmark_y_label(self,benchmark):
                
        data_list = [benchmark.resolution, benchmark.cpu_model , benchmark.gpu_model]
        
        if benchmark.game_quality_preset != "n.a.":
            data_list = [benchmark.game_quality_preset + " preset, at: "] + data_list
        
        if benchmark.additional_notes:
           
            data_list += [benchmark.additional_notes]
        
        y_tick_label = ", ".join(data_list)
            
        
        
        return unicode(y_tick_label)
        
        
    def __init__(self, *args, **kwargs):
        super(BenchmarkChartTable, self).__init__(*args, **kwargs)
        
        # compute the max fps median
        fps_medians = [x.fps_median for x in self.data.queryset]
        self.max_fps = float(max(fps_medians))
        
        self.base_columns['operating_system'].verbose_name = "OS"
        self.base_columns['operating_system'].attrs={"th": {"width": "10%"}}
        self.base_columns['game'].attrs={"th": {"width": "20%"}}
        self.base_columns['fps_median'].attrs={"th": {"width": "50%"}}

    class Meta:
        model = Benchmark
        fields = ("game","operating_system","fps_median")
        
    
    def render_game(self, value):
        return mark_safe('<a href="/benchmark_chart/?game=' + unicode(value.title) + '" >'+ unicode(value.title)+"</a>")
        
    def render_operating_system(self, record,value):
        if record.operating_system.lower().find("windows") != -1:
        
            return mark_safe('<a href="#" class="nounderline label label-primary" data-toggle="popover"  data-trigger="hover" title="OS" data-content="'+unicode(value)+'">'+value.split("(")[0]+'</a>')
        else:
            return mark_safe('<a href="#" class="nounderline label label-danger" data-toggle="popover" data-trigger="hover" title="OS" data-content="'+unicode(value)+'">'+value.split("(")[0]+'</a>')
        
        
    def render_fps_median(self, record, value):
        
        perc_val = (float(value) / self.max_fps) * 100
        
        col_linux = "#ff4136"
        col_windows = "#158cba"
        bar_col = col_linux
        if record.operating_system.lower().find("windows") != -1:
            bar_col = col_windows
                  
        data_content = self.set_benchmark_y_label(record).replace('"','&quot;')
        
        return mark_safe('<a class="nounderline" href="#" data-toggle="popover"  data-trigger="hover" title="Notes" data-placement="left" data-content="'+data_content+'"><div style="background:#DDDDDD; border:0px solid #666666;"><div style="padding-left: 5px; background: '+bar_col+'; width:'+str(perc_val)+'%;">'+str(value)+'</div></div></a>')
        
        
        
