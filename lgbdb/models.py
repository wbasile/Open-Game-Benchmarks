from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from .multiple_choice_options import *



class NewsPost(models.Model):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    body = models.TextField()
    posted = models.DateField(db_index=True, auto_now_add=True)
    
    def __unicode__(self):
        return '%s' % self.title

    def get_absolute_url(self):
        return ('view_blog_post', None, { 'slug': self.slug })




""" a system is a combination of hardware and software
each user can have multiple systems
when adding a benchmark, the user can select one of his systems
"""
@python_2_unicode_compatible
class System(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    descriptive_name = models.CharField(max_length=200,blank=False)
    
    # these should be present
    cpu_model = models.CharField(max_length=50,choices=CPU_CHOICES)
    gpu_model = models.CharField(max_length=50,choices=GPU_CHOICES)
    dual_gpu = models.CharField(max_length=50,choices=DUAL_GPU_CHOICES,default="None")
    resolution = models.CharField(max_length=50,choices=RESOLUTION_CHOICES)
    driver = models.CharField(max_length=50,choices=DRIVER_CHOICES)
    operating_system = models.CharField(max_length=80,choices=OS_CHOICES)
    
    
    # optional
    desktop_environment = models.CharField(max_length=60, blank=True)
    kernel = models.CharField(max_length=60, blank=True)
    gpu_driver_version = models.CharField(max_length=60, blank=True)
    
    additional_details = models.CharField(max_length=300, blank=True) # ex. overclocks
    
    def __str__(self):
        return self.descriptive_name



# small class representing a steam game
@python_2_unicode_compatible
class Game(models.Model):
    
    title = models.CharField(max_length=100)
    steam_appid = models.IntegerField(unique = True)
    
    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ('title',)
        
    

# the most important model; it represent a single benchmark test of a game
@python_2_unicode_compatible
class Benchmark(models.Model):
  
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    
    # this field is automatically filled with the currently logged in user id, when the user fills the add/edit benchmark form
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # instead of having a system field here, the logged in user can select one of his systems on the form,
    # and the internal data of the system are copied to the Benchmark
    cpu_model = models.CharField(max_length=50,choices=CPU_CHOICES,blank=True)
    gpu_model = models.CharField(max_length=50,choices=GPU_CHOICES,blank=True)
    dual_gpu = models.CharField(max_length=50,choices=DUAL_GPU_CHOICES,default="None")
    resolution = models.CharField(max_length=50,choices=RESOLUTION_CHOICES,blank=True)
    driver = models.CharField(max_length=50,choices=DRIVER_CHOICES,blank=True)
    operating_system = models.CharField(max_length=80,choices=OS_CHOICES,blank=True)
    
    
    desktop_environment = models.CharField(max_length=60,blank=True)
    kernel = models.CharField(max_length=60,blank=True)
    gpu_driver_version = models.CharField(max_length=60, blank=True)                                  
                
    
    
    game_quality_preset = models.CharField(max_length=20,
                                      choices=GAME_SETTINGS_CHOICES,
                                      default='LO')
    
    #antialias = models.CharField(max_length=50,choices=ANTIALIAS_CHOICES,default="Antialias enabled")
    
    additional_notes = models.CharField(max_length=1000, blank=True) # this field is optional
    
    
    
    # this is the fps file (from fraps, glxosd or voglperf)
    frames_file = models.FileField()
    
    # user cannot input those directly, rather, they are calculated as soon as the frames file is uploaded
    fps_data = models.CommaSeparatedIntegerField(max_length=1500,default = "")
    
    fps_min = models.IntegerField(default = 0.0)
    fps_max = models.IntegerField(default = 0.0)
    fps_avg = models.IntegerField(default = 0.0)
    fps_std = models.FloatField(default = 0.0)
    
    fps_1st_quartile = models.IntegerField(default = 0.0)
    fps_median = models.IntegerField(default = 0.0)
    fps_3rd_quartile = models.IntegerField(default = 0.0)

    length_seconds = models.IntegerField(default = 0) # length of the benchmark in milliseconds (it actually corresponds to len(fps_data)
  
    
    # this will not be set by the user when uploading
    upload_date = models.DateTimeField('upload date', auto_now=False, auto_now_add=True)
    change_date = models.DateTimeField('change date', auto_now=True, auto_now_add=False)
    
    
    def __str__(self):
        return slugify(self.game.title + " " + self.game_quality_preset +" "+ self.cpu_model +" "+ self.gpu_model) # +" "+ str(self.upload_date))
        #~ return self.game.title + " " str(self.upload_date)
    
    def get_absolute_url(self):
        return "/benchmark_detail/%i" % self.id
