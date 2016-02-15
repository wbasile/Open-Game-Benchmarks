from .models import Game, Benchmark

def navbargames_processor(request):
    navbargames = Game.objects.all()            
    return {'navbargames': navbargames}
