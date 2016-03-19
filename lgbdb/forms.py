from django import forms
from .models import System, Benchmark, Game, UserAvatar
from django.utils.safestring import mark_safe
import numpy as np
    
            
            
class UserAvatarAddEditForm(forms.ModelForm):
    class Meta:
        model = UserAvatar
        fields = '__all__'
        exclude = ['user']
        
        
    # this constructor allows this form to receive a user object as a constructor parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(UserAvatarAddEditForm, self).__init__(*args, **kwargs)
        self.fields['avatar'].label = "Image URL"
        
    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']

        try:
        
            #validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
                raise forms.ValidationError(u'Please use a JPEG, '
                    'GIF or PNG image.')

            #validate file size
            if len(avatar) > (500 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar
        
    
        

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        

def check_voglperf_format(lines):
    # check the length of the file
    if len(lines) <= 1: return False
    
    # check the format of the header
    ## example:  Dec 22 13:38:47 - isaac.x64
    header = lines[0]
    if header[0] != "#": return False
    if len(header.split("-")) <= 1: return False
    #~ print "Header OK"
    
    # check that every line is a float
    for l in lines[1:]:
        try: 
            f = float(l.replace(",","."))
        except:
            return False
            
    return True
    
    
def check_fraps_format(lines):
    if len(lines) <= 1: return False
    
    if lines[0].strip() == "FPS":
        return True
    return False
    

def check_glxosd_format(lines):
    if len(lines) <= 1: return False
    
    for line in lines:
        
        l = line.split(",")
        
        if len(l) != 2:
            return False
            
        if is_number(l[0]) == False: return False
        if is_number(l[1]) == False: return False
    
    return True



def get_file_format(lines):
    
    if check_voglperf_format(lines):
        return "voglperf"
    
    if check_fraps_format(lines):
        return "fraps"
        
    if check_glxosd_format(lines):
        return "glxosd"
        
    return None
    
    
# given a voglperf file, returns the timings
def parse_voglperf_to_fps(lines):
    
    # read the actual frame timings
    frames = [float(x.replace(",",".")) for x in lines[1:]]
    
    # calculate fps from the timings
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
            
    return fps
    
    
# given a fraps file, returns the timings
def parse_fraps_to_fps(lines):
    fps = [int(x) for x in lines[1:]]
    return fps
    
    
# given a glxosd file, returns the timings
def parse_glxosd_to_fps(lines):
    timings = []
    for l in lines:
        timings += [int(l.split(",")[1])]
        
    frames = []
    for i in range(1,len(timings)):
        frames += [(timings[i] - timings[i-1])/1000000.0] # yes, glxosd uses nanoseconds
    
    # calculate fps from the timings
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
            
    return fps


def parse_frames_file(frames_file):
    
    # read in the file
    lines = filter(None, frames_file.read().split("\n"))

    # check the format of the file
    file_format = get_file_format(lines)
    
 
    if not file_format:
        return None, []
        
    if file_format == "voglperf":
        fps = parse_voglperf_to_fps(lines)
    elif file_format == "fraps":
        fps = parse_fraps_to_fps(lines)
    elif file_format == "glxosd":
        fps = parse_glxosd_to_fps(lines)
    
    return file_format, fps



# a simple form, that holds the logic to process the uploaded timings file
class BenchmarkAddForm(forms.ModelForm):
    
    class Meta:
        model = Benchmark        
        
        fields = [  "game", "frames_file" ,"additional_notes", "game_quality_preset"]
        widgets = {'additional_notes': forms.Textarea(attrs={'cols': 80, 'rows': 10,"placeholder":"Comments about the benchmark. For example 'Antialias 8X', start of level 2', 'final boss', 'windowed mode'"})}
    
    
    # this allows this form to receive a user object as a constructor parameter
    def __init__(self, *args, **kwargs):
        
        self.user = kwargs.pop('user',None)
        super(BenchmarkAddForm, self).__init__(*args, **kwargs)
            
        # add a field to chose the system among the ones of the user    
        system_choices = [(k.id,k.descriptive_name + " (" + ", ".join([k.cpu_model, k.gpu_model, k.operating_system]) + ")") for k in self.user.system_set.all()]
                
        self.fields['user_system'] = forms.ChoiceField(required=True,choices=system_choices)
 
        # adjust some labels and help text
        self.fields['frames_file'].label = "Frames file"
        self.fields['additional_notes'].label += " (optional)"
               
        self.fields['game'].help_text = mark_safe('Select the game that you benchmarked')      
        self.fields['user_system'].help_text = mark_safe('Select one of your systems or <a href="/system_add" class="btn btn-xs btn-warning">Add a new system </a> if you do not have one')      
        self.fields['frames_file'].help_text = mark_safe("The output of VOGLPERF, GLXOSD or FRAPS (<b>fps.csv</b> file), a file containing the frame timings <br>Minimum 60 seconds, maximum 300 seconds (longer benchmarks will be trimmed)<br>")        
        self.fields['game_quality_preset'].help_text = mark_safe("The graphical quality settings used in this benchmark. If not applicable, select <b>n.a.</b>")
                
        # set the order of the fields in the form
        self.order_fields([ "game","user_system", "frames_file", "game_quality_preset" ,"additional_notes"])


    def clean(self):
        
        # get the game first
        game = self.cleaned_data.get('game')
            
        # check if the user has at least 1 system
        if len(self.user.system_set.all()) <= 0:
            raise forms.ValidationError("You must create a system first")

        
        # parse the frames file (voglperf)
        frames_file = self.cleaned_data.get('frames_file')
        
        if not frames_file:
            raise forms.ValidationError("You must upload a valid VOGLPERF, GLXOSD or FRAPS output file")


        # obtain the format and actual fps data
        file_format, fps = parse_frames_file(frames_file)
        
        if not file_format:
            raise forms.ValidationError("The file: " + frames_file.name + " does not seem to be a valid VOGLPERF, GLXOSD or FRAPS output")
        
        if not fps:
            raise forms.ValidationError("The file: " + frames_file.name + " does not seem to be a valid VOGLPERF, GLXOSD or FRAPS output")

            
        # VOGLPERF: here we could do some double check on the game, because the name of the file contains the steam appid of the game
        #~ if file_format == "voglperf":
            #~ 
            #~ #process the name to get the game
            #~ start_pos = frames_file.name.find("voglperf")
            #~ game_appid = frames_file.name[start_pos:].split(".")[1].replace("gameid","")
            #~ #check if the steam appid is an integer 
            #~ try:
                #~ game_appid = int(game_appid)
            #~ except ValueError:
                #~ raise forms.ValidationError("Something strange happened: the game of your VOGLPERF file is not valid. Did you rename the file?")
            #~ 
            #~ if game_appid not in [x[0] for x in Game.objects.values_list("steam_appid")]:
                #~ raise forms.ValidationError("Something strange happened: the game of your VOGLPERF file does not match any in the database")
            #~ 
            #~ if game_appid != game.steam_appid:
                #~ raise forms.ValidationError("The game of your VOGLPERF file does not match the one you have selected. Maybe you choose the wrong game or file? ")
            
       
    
                
        # limit the fps to 300, i.e. 5 minutes
        if len(fps) > 300:
            fps = fps[0:300]

        # raise an error or warning if the duration is below a certain threshold
        duration_cutoff = 59
        if len(fps) < duration_cutoff:
            raise forms.ValidationError("The duration of the benchmark should be at least " + str(duration_cutoff) + " seconds (your test is " + str(len(fps)) + "s)")

        # from fps calculate all sort of statistical measures
        fps_min = min(fps)
        fps_max = max(fps)
        fps_avg = round(np.mean(fps),1)
        fps_std = np.std(fps)
        
        fps_1st_quartile = np.percentile(fps, 25)
        fps_median = np.percentile(fps, 50)
        fps_3rd_quartile = np.percentile(fps, 75)

        
        # create the missing fields of the instance
        
        # use a comma separated string to store the fps data
        self.instance.fps_data = ",".join([str(x) for x in fps])
        
        self.instance.fps_avg =  fps_avg
        self.instance.fps_min =  fps_min
        self.instance.fps_max =  fps_max
        self.instance.fps_std =  fps_std
        
        self.instance.fps_1st_quartile = fps_1st_quartile
        self.instance.fps_median = fps_median
        self.instance.fps_3rd_quartile = fps_3rd_quartile
        
        self.instance.length_seconds =  len(fps)
        
        # from the user system get all the hardware and software details
        us = System.objects.get(id=self.cleaned_data["user_system"])
        
        self.instance.cpu_model = us.cpu_model
        self.instance.gpu_model = us.gpu_model
        self.instance.dual_gpu = us.dual_gpu
        self.instance.resolution = us.resolution
        self.instance.driver = us.driver
        self.instance.operating_system = us.operating_system
        self.instance.desktop_environment = us.desktop_environment
        self.instance.kernel = us.kernel
        self.instance.gpu_driver_version = us.gpu_driver_version

        return self.cleaned_data 
    



class BenchmarkEditForm(forms.ModelForm):
    
        
    class Meta:
        model = Benchmark        
        #~ fields = '__all__'
        exclude = ['user','frames_file','fps_data']
        widgets = {'additional_notes': forms.Textarea(attrs={'cols': 80, 'rows': 10})}


    def __init__(self, *args, **kwargs):
        
        super(BenchmarkEditForm, self).__init__(*args, **kwargs)

        # make sure that the use does not edit FPS data
        for f in ['fps_min','fps_avg', 'fps_std', 'fps_max','fps_median', 'fps_1st_quartile','fps_3rd_quartile','length_seconds']:
            self.fields[f].widget.attrs['readonly'] = True
            self.fields[f].label = self.fields[f].label.replace("Fps", "FPS")
            
        # specify field order here
        self.order_fields([ "game", "game_quality_preset" ,"resolution",'fps_avg','fps_std', 'fps_min', "fps_1st_quartile", "fps_median","fps_3rd_quartile", 'fps_max','length_seconds',"cpu_model", "gpu_model","dual_gpu","driver","gpu_driver_version", "operating_system","desktop_environment", "kernel", "additional_notes"])

        #TODO: correct capitalization here
        # correct capitalization fro acronyms
        self.fields['cpu_model'].label = "CPU Model"
        self.fields['gpu_model'].label = "GPU Model"
        self.fields['dual_gpu'].label = "Dual GPU"
        
        
        
class SystemAddEditForm(forms.ModelForm):
    
    class Meta:
        model = System        
        fields = '__all__'
        exclude = ['user']
        
        widgets =   {
                    'descriptive_name': forms.TextInput(attrs={'placeholder': "ex. Gaming desktop, Laptop"}),
                    'desktop_environment': forms.TextInput(attrs={'placeholder': "ex. KDE, GNOME, Cinnamon, Aero (for Windows)"}),
                    'kernel': forms.TextInput(attrs={'placeholder': "ex. x86_64 Linux 3.16.0-38-generic"}),
                    'gpu_driver_version': forms.TextInput(attrs={'placeholder': "ex. NVidia 361.18"}),
                    'additional_details': forms.Textarea(attrs={'cols': 80, 'rows': 4,"placeholder":"Details about the system. For example CPU/GPU overclock, RAM, quadruple monitor"}),
                    }
      
        
        
    # this constructor allows this form to receive a user object as a constructor parameter
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(SystemAddEditForm, self).__init__(*args, **kwargs)
         
        self.fields["driver"].label = "GPU Driver"
        
        self.fields["desktop_environment"].label = "Desktop Environment (optional)"
        self.fields["kernel"].label = "Linux kernel (optional)"
        self.fields["gpu_driver_version"].label = "GPU Driver version (optional)"
        self.fields["additional_details"].label = "Additional details (optional)"
             
        self.fields['descriptive_name'].help_text = "You can give to your system any name; keep it easy to remember"
        self.fields['cpu_model'].help_text = "On Linux you can use <code>cat /proc/cpuinfo | grep 'model name' | uniq</code> to find out the model of your CPU"
        self.fields['gpu_model'].help_text = "On Linux you can use <code>lspci -vnn | grep VGA</code> to find out the model of your GPU"
        self.fields['resolution'].help_text = "On Linux you can use <code>xrandr</code> to find out your current resolution"
        self.fields['kernel'].help_text = "On Linux you can use <code>uname -mr</code> to find out your Kernel version"
        
        # correct capitalization fro acronyms
        self.fields['cpu_model'].label = "CPU Model"
        self.fields['gpu_model'].label = "GPU Model"
        self.fields['dual_gpu'].label = "Dual GPU"
            
