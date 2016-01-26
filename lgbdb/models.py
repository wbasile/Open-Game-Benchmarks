from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from .multiple_choice_options import *

 

@python_2_unicode_compatible
class System(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    descriptive_name = models.CharField(max_length=200,blank=False)
    
    # these should be present
    cpu_model = models.CharField(max_length=50,choices=CPU_CHOICES)
    gpu_model = models.CharField(max_length=50,choices=GPU_CHOICES)
    resolution = models.CharField(max_length=50,choices=RESOLUTION_CHOICES)
    driver = models.CharField(max_length=50,choices=DRIVER_CHOICES)
    operative_system = models.CharField(max_length=80,choices=OS_CHOICES,default="Linux-other")
    
    # these might be optional
    #~ linux_distribution = models.CharField(max_length=50, blank=True)
    #~ desktop_environment = models.CharField(max_length=50, blank=True)
    #~ window_manager = models.CharField(max_length=50,  blank=True)
    #~ kernel = models.CharField(max_length=50, blank=True)
    
        
    def __str__(self):
        return self.descriptive_name


@python_2_unicode_compatible
class Game(models.Model):
    
    
    title = models.CharField(max_length=100)
    steam_appid = models.IntegerField(unique = True)
    
    # this is a "static" field instead of being computed on the fly, because in this way django-tables2 is able to sort the game tale by it
    num_benchmarks = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ('title',)
        
    
        
        

        
@python_2_unicode_compatible
class Benchmark(models.Model):
  
    # this field should automatically be filled with the currently logged in user id, when the user fills the form
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # instead of having a system field here, the logged in user can select one of his systems on the form,
    # and the internal data of the system are copied to the GameBenchmark
    
    cpu_model = models.CharField(max_length=50,choices=CPU_CHOICES,blank=True)
    gpu_model = models.CharField(max_length=50,choices=GPU_CHOICES,blank=True)
    resolution = models.CharField(max_length=50,choices=RESOLUTION_CHOICES,blank=True)
    driver = models.CharField(max_length=50,choices=DRIVER_CHOICES,blank=True)
    operative_system = models.CharField(max_length=50,choices=OS_CHOICES,blank=True)
     
    #~ linux_distribution = models.CharField(max_length=50,blank=True)
    #~ desktop_environment = models.CharField(max_length=50,blank=True)
    #~ window_manager = models.CharField(max_length=50,blank=True)
    #~ kernel = models.CharField(max_length=50,blank=True)
                                      
                    
    GAME_SETTINGS_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('n.a.', 'n.a.'),
    )
    
    game_quality_preset = models.CharField(max_length=20,
                                      choices=GAME_SETTINGS_CHOICES,
                                      default='LO')
    
    
    
    additional_notes = models.CharField(max_length=300, blank=True) # this field is optional
    
    
    
    # this is the VOGLPERF output file
    frames_file = models.FileField()
    
    # user cannot input those directly, rather, they are calculated as soon as the frames file is uploaded
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    
    fps_data = models.CommaSeparatedIntegerField(max_length=300,default = "")
    
    fps_min = models.IntegerField(default = 0.0)
    fps_max = models.IntegerField(default = 0.0)
    fps_avg = models.IntegerField(default = 0.0)
    fps_std = models.FloatField(default = 0.0)
    
    fps_1st_quartile = models.FloatField(default = 0.0)
    fps_median = models.FloatField(default = 0.0)
    fps_3rd_quartile = models.FloatField(default = 0.0)



    #~ fps_graph = models.ImageField(blank=True)
    length_seconds = models.IntegerField(default = 0) # length of the benchmark in milliseconds
  
    
    # this will not be set by the user when uploading
    upload_date = models.DateTimeField('upload date', auto_now=False, auto_now_add=True)
    change_date = models.DateTimeField('change date', auto_now=True, auto_now_add=False)
    
    
    # used to automatically update the number of benchmark of a specific game
    #~ def save(self, *args, **kwargs):
        #~ super(Benchmark, self).save(*args,**kwargs)
                #~ 
        #~ # update game num benchmarks
        #~ if self.id:
            #~ self.game.num_benchmarks=len(self.game.benchmark_set.all())
            #~ self.game.save()
        #~ 
    
    def __str__(self):
        return slugify(self.game.title + " " + self.game_quality_preset +" "+ self.cpu_model +" "+ self.gpu_model) # +" "+ str(self.upload_date))
        #~ return self.game.title + " " str(self.upload_date)
    
    
