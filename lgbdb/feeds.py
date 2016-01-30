from django.contrib.syndication.views import Feed
from models import Benchmark

class LatestBenchmarks(Feed):
    title = "Open Game Benchmarks latest submissions"
    link = "/"

    def items(self):
        return Benchmark.objects.all().order_by("-upload_date")[0:10]

    def item_title(self, item):
        return unicode(item.game.title)

    def item_description(self, item):
        return ", ".join([unicode(x) for x in [ item.cpu_model, item.gpu_model, "settings: "+item.game_quality_preset, item.operating_system]])
