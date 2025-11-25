from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Recipient
from .forms import RecipientForm


class OwnerFilteredMixin(LoginRequiredMixin):
    """Фильтруем клиентов по владельцу; менеджер с perm 'clients.view_all_recipients' видит всех."""

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.has_perm("clients.view_all_recipients") or u.is_superuser:
            return qs
        return qs.filter(owner=u)


class OwnerOnlyMutationMixin:
    """Изменять/удалять можно только свои записи (или суперпользователь)."""

    def dispatch(self, request, *args, **kwargs):
        if self.request.method.lower() in ("post", "put", "patch", "delete"):
            obj = self.get_object()
            u = self.request.user
            if not (u.is_superuser or obj.owner_id == u.id):
                messages.error(request, "Нельзя изменять чужого клиента.")
                return reverse_lazy("clients:recipient_list")
        return super().dispatch(request, *args, **kwargs)


class RecipientListView(OwnerFilteredMixin, ListView):
    """Список получателей (по владельцу/или все при праве)."""

    model = Recipient
    template_name = "clients/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 10


class RecipientDetailView(OwnerFilteredMixin, DetailView):
    """Детали получателя (с учётом владельца/прав)."""

    model = Recipient
    template_name = "clients/recipient_detail.html"
    context_object_name = "recipient"


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Создание получателя. Владелец = текущий пользователь."""

    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.save()
        messages.success(self.request, "Получатель успешно добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(OwnerFilteredMixin, OwnerOnlyMutationMixin, UpdateView):
    """Редактирование только своего получателя (или суперпользователь)."""

    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        messages.success(self.request, "Данные получателя обновлены.")
        return super().form_valid(form)


class RecipientDeleteView(OwnerFilteredMixin, OwnerOnlyMutationMixin, DeleteView):
    """Удаление только своего получателя (или суперпользователь)."""

    model = Recipient
    template_name = "clients/recipient_confirm_delete.html"
    success_url = reverse_lazy("clients:recipient_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Получатель удалён.")
        return super().delete(request, *args, **kwargs)
