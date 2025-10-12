from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ModelForm
from django.forms.widgets import DateTimeInput

from .models import Event


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start', 'end', 'is_all_day']
        widgets = {
            'start': DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Formato que o <input type="datetime-local"> envia
        fmt = '%Y-%m-%dT%H:%M'
        self.fields['start'].input_formats = [fmt]
        self.fields['end'].input_formats = [fmt]
        self._user = user  # guardamos o usuário para o save()

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.owner = self._user
        if commit:
            obj.save()
        return obj


@login_required(login_url='/admin/login/')
def event_list_view(request):
    events = Event.objects.filter(owner=request.user).order_by('start')
    return render(request, "scheduler/events.html", {"events": events})


@login_required(login_url='/admin/login/')
def event_create_view(request):
    if request.method == "POST":
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Evento "{event.title}" criado com sucesso!')
            return redirect("scheduler_web:events")
    else:
        form = EventForm(user=request.user)
    return render(request, "scheduler/event_form.html", {"form": form})


@login_required(login_url='/admin/login/')
def event_detail_view(request, pk):
    e = get_object_or_404(Event, pk=pk, owner=request.user)
    return render(request, "scheduler/event_detail.html", {"e": e})
