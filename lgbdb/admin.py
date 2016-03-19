from django.contrib import admin
from .models import System ,Benchmark, Game, NewsPost, UserAvatar

# Register your models here.
admin.site.register(System)
admin.site.register(Benchmark)
admin.site.register(Game)
admin.site.register(NewsPost)
admin.site.register(UserAvatar)
