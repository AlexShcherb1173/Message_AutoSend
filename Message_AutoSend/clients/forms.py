from django import forms
from .models import Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_full_name(self):
        name = self.cleaned_data["full_name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("ФИО должно быть не короче 3 символов.")
        return name
5) Представления (CBV) + флеш-сообщения и пагинация
clients/views.py

python
Копировать код
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import RecipientForm
from .models import Recipient


class RecipientListView(ListView):
    model = Recipient
    template_name = "clients/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 10  # пагинация


class RecipientDetailView(DetailView):
    model = Recipient
    template_name = "clients/recipient_detail.html"
    context_object_name = "recipient"


class RecipientCreateView(CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        messages.success(self.request, "Получатель успешно добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        messages.success(self.request, "Данные получателя обновлены.")
        return super().form_valid(form)


class RecipientDeleteView(DeleteView):
    model = Recipient
    template_name = "clients/recipient_confirm_delete.html"
    success_url = reverse_lazy("clients:recipient_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Получатель удалён.")
        return super().delete(request, *args, **kwargs)