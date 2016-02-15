import django_filters
from django import forms

from django.db.models import Count

from .models import Benchmark, Game




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
    
    show = django_filters.MethodFilter(widget=forms.Select(choices=SHOW_CHOICES))

    
    class Meta:
        model = Game
        
        # these fields work even if the relative fields are hidden (excluded in the table)
        fields = ["title", "show"]
        
    
    # a function called by the "show" filter field, to generate a queryset based on a  given value    
    def filter_show(self, queryset, value):
        
        if value == "1":
            return queryset.annotate(num_benchmarks=Count('benchmark')).filter(num_benchmarks__gt=0)
        elif value == "2":
            return queryset.annotate(num_benchmarks=Count('benchmark')).filter(num_benchmarks=0)
        else:
            return queryset






# create a filter for Benchmarks
class BenchmarkFilter(django_filters.FilterSet):
    
    game = django_filters.MethodFilter(lookup_type='icontains')
            
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
        
  
        # correct capitalization in the labels
        self.filters['cpu_model'].label = "CPU Model"        
        self.filters['gpu_model'].label = "GPU Model"     
        
   
        
    def filter_game(self, queryset, value):
        if not value:   
            return queryset
                
        c_game = Game.objects.filter(title__icontains = value)
      
        return queryset.filter(game__in=c_game)
            

