from django import forms
from .models import System, Benchmark, Game
from django.utils.safestring import mark_safe
import numpy as np


def check_voglperf_format(lines):
    # check the length of the file
    if len(lines) <= 1: return False
    print "Length OK"
    
    # check the format of the header
    ## example:  Dec 22 13:38:47 - isaac.x64
    header = lines[0]
    if header[0] != "#": return False
    if len(header.split("-")) <= 1: return False
    print "Header OK"
    
    # check that every line is a float
    for l in lines[1:]:
        try: 
            f = float(l)
        except:
            return False
            
    print "Lines OK"
    return True




class BenchmarkAddForm(forms.ModelForm):
    
        
    class Meta:
        model = Benchmark        
        #~ fields = '__all__'
        
        fields = [  "frames_file" ,"additional_notes", "game_quality_preset"]
        widgets = {'additional_notes': forms.Textarea(attrs={'cols': 80, 'rows': 10,"placeholder":"Comments about the benchmark. For example 'start of level 2', 'final boss', 'windowed mode'"})}
    
    
    
    # this allows this form to receive a user object as a constructor parameter
    def __init__(self, *args, **kwargs):
        
        self.user = kwargs.pop('user',None)
        super(BenchmarkAddForm, self).__init__(*args, **kwargs)
            
        # add a field to chose the system among the ones of the user    
        queryset=self.user.system_set.all()
                
        self.fields['user_system'] = forms.ModelChoiceField(required=True,queryset=queryset, initial=queryset)
        self.order_fields([ "user_system", "frames_file", "game_quality_preset" ,"additional_notes"])

        self.fields['frames_file'].label = "Frames file"
        self.fields['additional_notes'].label += " (optional)"
               
        self.fields['user_system'].help_text = mark_safe('Select one of your systems or <a href="/system_add" class="btn btn-xs btn-warning">Add a new system </a> if you do not have one')      
        self.fields['frames_file'].help_text = "The output of VOGLPERF or FRAPS, a file containing the frame timings <br><b>WARNING! FRAPS is not supported yet!</b>"        
        self.fields['game_quality_preset'].help_text = "The graphical quality settings used in this benchmark. If not applicable, select <b>n.a.</b>"        
                
            

    def clean(self):
            
        # check if the user has at least 1 system
        if len(self.user.system_set.all()) <= 0:
            raise forms.ValidationError("You must create a system first")
        
        # parse the frames file (voglperf)
        frames_file = self.cleaned_data.get('frames_file')
        if not frames_file:
            raise forms.ValidationError("You must upload a valid voglperf output file")
        
        
        lines = filter(None, frames_file.read().split("\n"))
        
        # check the format of the file
        if check_voglperf_format(lines) == False:
            raise forms.ValidationError("The file: " + frames_file.name + " does not seem to be a valid voglperf output")
        
        
        
        #~ process the name to get the game
        start_pos = frames_file.name.find("voglperf")
        game_appid = frames_file.name[start_pos:].split(".")[1].replace("gameid","")
        
        #~ check if the steam appid is an integer 
        try:
            game_appid = int(game_appid)
        except ValueError:
            raise forms.ValidationError("The Steam App ID " + str(game_appid) + " is not valid (not an integer)")
            
        
        # if game_appid is not in our db, raise an exception
        current_appid_list = []
        for g in Game.objects.values():
            a = g['steam_appid']
            current_appid_list +=[a]
            
        if int(game_appid) not in current_appid_list:
            raise forms.ValidationError("The Steam App ID " + str(game_appid) + " is not in the database")
            
        # finally return the correct game    
        g = Game.objects.get(steam_appid=game_appid)
        
        print "Adding benchmark for game: " 
        print g
        
        
        
        # read the actual frame timings
        frames = [float(x) for x in lines[1:]]


        # calculate fps
        timecounter = 0
        framecount = 0
        
        fps = []
        for f in frames:
            timecounter += f
            framecount += 1
            if timecounter >= 1000:
                fps += [framecount]
                timecounter = 0
                framecount = 0
                
                
        # limit the fps to 300, i.e. 5 minutes
        if len(fps) > 300:
            fps = fps[0:300]

        # from fps calculate all sort of statistical measures
        fps_min = min(fps)
        fps_max = max(fps)
        fps_avg = round(np.mean(fps),1)
        fps_std = np.std(fps)
        
        
        fps_1st_quartile = np.percentile(fps, 25)
        fps_median = np.percentile(fps, 50)
        fps_3rd_quartile = np.percentile(fps, 75)
        
        
        total_seconds = int(round(sum(frames) / 1000,0))
        
        # raise an error or warning if the duration is below a certain threshold
        duration_cutoff = 60
        if total_seconds < duration_cutoff:
            raise forms.ValidationError("The duration of the benchmark should be at least " + str(duration_cutoff) + " seconds (your test is " + str(total_seconds) + "s)")
        
        
        
        # updated the returned dictionary
        
        self.instance.fps_data = ",".join([str(x) for x in fps])
        
        self.instance.fps_avg =  fps_avg
        self.instance.fps_min =  fps_min
        self.instance.fps_max =  fps_max
        self.instance.fps_std =  fps_std
        
        self.instance.fps_1st_quartile = fps_1st_quartile
        self.instance.fps_median = fps_median
        self.instance.fps_3rd_quartile = fps_3rd_quartile
        
        self.instance.length_seconds =  total_seconds
        self.instance.game =  g
        
        
        # from the user system get all the hardware and software details
        us = self.cleaned_data["user_system"]
        
        self.instance.cpu_model = us.cpu_model
        self.instance.gpu_model = us.gpu_model
        self.instance.resolution = us.resolution
        self.instance.driver = us.driver
        self.instance.operative_system = us.operative_system
        #~ self.instance.window_manager = us.window_manager
        #~ self.instance.kernel = us.kernel
        #~ self.instance.linux_distribution = us.linux_distribution
        
    
        g.num_benchmarks = g.num_benchmarks + 1 
        g.save()




class BenchmarkEditForm(forms.ModelForm):
    
        
    class Meta:
        model = Benchmark        
        #~ fields = '__all__'
        exclude = ['game','user','frames_file','fps_data']
        widgets = {'additional_notes': forms.Textarea(attrs={'cols': 80, 'rows': 10})}



    def __init__(self, *args, **kwargs):
        
        super(BenchmarkEditForm, self).__init__(*args, **kwargs)

        for f in ['fps_min','fps_avg', 'fps_std', 'fps_max','fps_median', 'fps_1st_quartile','fps_3rd_quartile','length_seconds']:
            self.fields[f].widget.attrs['readonly'] = True

        # TODO: specify field order here
        #~ self.order_fields([  "game_quality_preset" ,"additional_notes", 'fps_min','fps_avg', 'fps_std', 'fps_max','length_seconds'])




class SystemAddEditForm(forms.ModelForm):
    
    #~ stuff = forms.ChoiceField( [('a','A'),('b','B')], widget = forms.Select(attrs = {'onclick' : "alert('foo !');"}))
        
    class Meta:
        model = System        
        fields = '__all__'
        exclude = ['user']
        
        widgets =   {
                    'descriptive_name': forms.TextInput(attrs={'placeholder': "ex. Gaming desktop, Laptop"}),
                    #~ 'linux_distribution': forms.TextInput(attrs={'placeholder': "ex. Ubuntu, Arch, Mint"}),
                    #~ 'desktop_environment': forms.TextInput(attrs={'placeholder': "ex. KDE, GNOME, Cinnamon"}),
                    #~ 'window_manager': forms.TextInput(attrs={'placeholder': "ex. KWin, Marco"}),
                    #~ 'kernel': forms.TextInput(attrs={'placeholder': "ex. x86_64 Linux 3.16.0-38-generic"})
                    }
        
        
    # this constructor allows this form to receive a user object as a constructor parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(SystemAddEditForm, self).__init__(*args, **kwargs)
         
        self.fields["driver"].label = "GPU Driver"
        
        #~ for field_name in ['descriptive_name','cpu_model', 'gpu_model','resolution', 'driver']:
            #~ self.fields[field_name].label = self.fields[field_name].label + "*"
        #~ self.order_fields([ "user_system", "frames_file" ,"additional_notes"])
     
        self.fields['descriptive_name'].help_text = "You can give to your system any name; keep it easy to remember"
        self.fields['cpu_model'].help_text = "On Linux you can use <code>cat /proc/cpuinfo | grep 'model name' | uniq</code> to find out the model of your CPU"
        self.fields['gpu_model'].help_text = "On Linux you can use <code>lspci -vnn | grep VGA</code> to find out the model of your CPU"
        self.fields['resolution'].help_text = "On Linux you can use <code>xrandr</code> to find out your current resolution"
        
            
            
