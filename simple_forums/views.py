from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import generic

from simple_forums import forms, models
from simple_forums.backends.search import simple_search
from simple_forums.utils import thread_detail_url

from django.contrib.auth.decorators import login_required


from django.utils import timezone
from django.core.urlresolvers import reverse

try:
    from django.contrib.auth.mixins import LoginRequiredMixin
except ImportError:
    from simple_forums.compatability.mixins import LoginRequiredMixin


class SearchView(generic.View):
    """ View for searching """

    template_name = 'simple_forums/search.html'
    query_kwarg = 'q'

    def get(self, request, *args, **kwargs):
        """ Show the search form and results if applicable """
        self.args = args
        self.kwargs = kwargs
        self.request = request

        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = dict()

        query = self.get_query()
        if query is not None:
            context['query'] = query
            context['results'] = self.get_queryset()

        return context

    def get_query(self):
        """ Return the query passed as a GET parameter """
        return self.request.GET.get(self.query_kwarg, None)

    def get_queryset(self):
        """ Return the list of threads that match the query """
        backend = simple_search.SimpleSearch()

        return backend.search(self.get_query())


class ThreadCreateView(LoginRequiredMixin, generic.edit.FormView):
    """ View for creating new threads """

    template_name = 'simple_forums/thread_create.html'
    form_class = forms.ThreadCreationForm

    def form_valid(self, form):
        """ Save form if it is valid """
        thread = form.save(self.request.user)

        return HttpResponseRedirect(thread_detail_url(thread=thread))


class ThreadDetailView(generic.DetailView):
    """ View for getting a thread's details """

    model = models.Thread
    pk_url_kwarg = 'thread_pk'

    def get_context_data(self, **kwargs):
        context = super(ThreadDetailView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            context['reply_form'] = forms.ThreadReplyForm()
            
        return context

    def post(self, request, *args, **kwargs):
        """ Create a new reply to the current thread """
        if not request.user.is_authenticated():
            raise PermissionDenied()

        self.object = self.get_object()

        form = forms.ThreadReplyForm(request.POST)

        if form.is_valid():
            form.save(request.user, self.object)

            return HttpResponseRedirect(thread_detail_url(thread=self.object))

        context = self.get_context_data()
        context['reply_form'] = form
        
        return render(request, self.get_template_names(), context)



class ThreadListView(generic.ListView):
    """ View for listing threads """

    model = models.Thread
    reverse_kwarg = 'rev'
    sort_default = 'activity'
    sort_default_reverse = True
    sort_mapping = {
        'activity': 'time_last_activity',
        'title': 'title',
    }
    sort_kwarg = 'sort'

    def get_context_data(self, **kwargs):
        context = super(ThreadListView, self).get_context_data(**kwargs)

        context['sort_current'] = self.sort_name
        context['sort_options'] = [item for item in self.sort_mapping]
        context['sort_reversed'] = self.sort_reversed

        sticky_threads = self._get_base_queryset().filter(sticky=True)
        context['sticky_thread_list'] = sticky_threads

        topic = get_object_or_404(
            models.Topic,
            pk=self.kwargs.get('topic_pk'))
        context['topic'] = topic

        return context

    def _get_base_queryset(self):
        """ Retrieve all threads associated with the given topic """
        topic = get_object_or_404(
            models.Topic,
            pk=self.kwargs.get('topic_pk'))

        return self.model.objects.filter(topic=topic)

    def get_queryset(self):
        """ Return all non-sticky threads """
        self.sort_name = self.request.GET.get(
            self.sort_kwarg,
            None)

        if self.sort_name not in self.sort_mapping:
            self.sort_name = 'activity'
            self.sort_reversed = True
        else:
            self.sort_reversed = self.request.GET.get(
                self.reverse_kwarg, None) == 'true'

        self.sort_field = self.sort_mapping.get(self.sort_name)

        if self.sort_reversed:
            self.sort_field = '-%s' % self.sort_field

        queryset = self._get_base_queryset()
        # exclude sticky posts
        queryset = queryset.exclude(sticky=True)
        # apply sorting
        queryset = queryset.order_by(self.sort_field)

        return queryset



class TopicListView(generic.ListView):
    """ View for listing topics """

    model = models.Topic
    
    def get_context_data(self, **kwargs):
        context = super(TopicListView, self).get_context_data(**kwargs)


        latest_threads = []
        thread_counts = []
        for t in models.Topic.objects.all():
            all_threads = t.thread_set.all().order_by("-time_last_activity")
            if all_threads:
                latest_threads += [(t,all_threads[0])]
                
            thread_counts += [(t, len(all_threads))]
                
        context['latest_threads'] = latest_threads
        context['thread_counts'] = thread_counts
        
        return context




@login_required    
def ForumMessageEditView(request, pk=None):
    
    message = get_object_or_404(models.Message, pk=pk) # try to get the instance
    if message.user != request.user: # check if the instance belongs to the requesting user
        return HttpResponseForbidden("Forbidden")


    if request.method == 'POST':
        
        form = forms.ForumMessageEditForm(request.POST, instance=message)
            
        if form.is_valid():
            # ensure that the owner of this system is the current user
            instance = form.save(commit=False)
            instance.user = request.user
            instance.time_created = timezone.now()
            instance.save()
                
            return HttpResponseRedirect(reverse('thread-detail', args=[instance.thread.topic.pk,instance.thread.topic.slug,instance.thread.pk,instance.thread.slug]))

    else:
        form = forms.ForumMessageEditForm(instance=message)
            
                
    
    context = {'message':message, "form":form }
    
    template = "simple_forums/forum_message_edit.html"
        
    return render(request, template ,context)     
    
    
# page to delete a forum message
def ForumMessageDeleteView(request, pk=None):
    
    message = get_object_or_404(models.Message, pk=pk)
    
    if message.user != request.user:  
        return HttpResponseForbidden("Forbidden")
        
    if request.method == "POST":
        
        thread = message.thread
        message.delete()
        
        if thread.message_set.count() > 0:
        
            return HttpResponseRedirect(reverse('thread-detail', args=[thread.topic.pk,thread.topic.slug,thread.pk,thread.slug]))
        
        # if we deleted the last message of the thread, delete the thread itself
        else:
            topic = thread.topic
            thread.delete()
            return HttpResponseRedirect(reverse('thread-list', args=[topic.pk,topic.slug]))
            
            
    
    #~ form = forms.ForumMessageEditForm(instance=message)    
    
    return render(request, "simple_forums/forum_message_delete.html", {'message':message})


