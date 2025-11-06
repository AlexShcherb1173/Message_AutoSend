from __future__ import annotations
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.urls import reverse_lazy
from .models import Recipient

class RecipientListView(ListView):
    """Список всех получателей."""
    model = Recipient
    template_name = "clients/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 20


class RecipientDetailView(DetailView):
    """Просмотр одного получателя."""
    model = Recipient
    template_name = "clients/recipient_detail.html"
    context_object_name = "recipient"


class RecipientCreateView(CreateView):
    """Создание нового получателя."""
    model = Recipient
    template_name = "clients/recipient_form.html"
    fields = ["name", "email", "phone"]  # укажи поля из твоей модели Recipient
    success_url = reverse_lazy("clients:recipient_list")


class RecipientUpdateView(UpdateView):
    """Редактирование существующего получателя."""
    model = Recipient
    template_name = "clients/recipient_form.html"
    fields = ["name", "email", "phone"]
    success_url = reverse_lazy("clients:recipient_list")


class RecipientDeleteView(DeleteView):
    """Удаление получателя."""
    model = Recipient
    template_name = "clients/recipient_confirm_delete.html"
    success_url = reverse_lazy("clients:recipient_list")
