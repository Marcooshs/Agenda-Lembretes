from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.forms.widgets import DateTimeInput
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseBadRequest

from .models import Event


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start', 'end', 'is_all_day']
        widgets = {
            # habilita o picker nativo do navegador (datetime-local)
            'start': DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formato que o <input type="datetime-local"> envia (ex.: 2025-10-08T14:30)
        fmt = '%Y-%m-%dT%H:%M'
        self.fields['start'].input_formats = [fmt]
        self.fields['end'].input_formats = [fmt]


@login_required(login_url='/admin/login/')
def event_list(request):
    events = Event.objects.filter(owner=request.user).order_by('start')
    return render(request, 'htmx/event_list.html', {'events': events})


@login_required(login_url='/admin/login/')
def event_row(request, pk):
    e = get_object_or_404(Event, pk=pk, owner=request.user)
    return render(request, 'htmx/_event_row.html', {'e': e})


@login_required(login_url='/admin/login/')
@require_POST
def event_create(request):
    form = EventForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('Form inválido')
    e = form.save(commit=False)
    e.owner = request.user
    e.save()
    # retorna apenas a linha (partial) para o HTMX inserir na tabela
    return event_row(request, e.pk)


@login_required(login_url='/admin/login/')
@require_POST
def event_delete(request, pk):
    e = get_object_or_404(Event, pk=pk, owner=request.user)
    e.delete()
    # 204 faz o HTMX remover a <tr> automaticamente quando hx-swap="delete"
    return HttpResponse(status=204)
