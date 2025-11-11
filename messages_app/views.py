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

from .models import Message
from .forms import MessageForm


class OwnerFilteredMixin(LoginRequiredMixin):
    """Показываем все только при perms 'messages_app.view_all_messages'."""

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.has_perm("messages_app.view_all_messages") or u.is_superuser:
            return qs
        return qs.filter(owner=u)


class OwnerOnlyMutationMixin:
    """Разрешаем изменять/удалять только свои объекты (или суперпользователь)."""

    def dispatch(self, request, *args, **kwargs):
        if self.request.method.lower() in ("post", "put", "patch", "delete"):
            obj = self.get_object()
            u = self.request.user
            if not (u.is_superuser or obj.owner_id == u.id):
                messages.error(request, "Нельзя изменять чужой объект.")
                return reverse_lazy("messages_app:message_list")
        return super().dispatch(request, *args, **kwargs)


class MessageListView(OwnerFilteredMixin, ListView):
    """Список сообщений (по владельцу/или все при праве)."""

    model = Message
    template_name = "messages_app/message_list.html"
    context_object_name = "messages_list"
    paginate_by = 10


class MessageDetailView(OwnerFilteredMixin, DetailView):
    """Детали сообщения (доступ по владельцу или правам)."""

    model = Message
    template_name = "messages_app/message_detail.html"
    context_object_name = "message"


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения. Владелец = текущий пользователь."""

    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        obj.save()
        messages.success(self.request, "Сообщение создано.")
        return super().form_valid(form)


class MessageUpdateView(OwnerFilteredMixin, OwnerOnlyMutationMixin, UpdateView):
    """Редактирование только своего сообщения (или суперпользователь)."""

    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        messages.success(self.request, "Сообщение обновлено.")
        return super().form_valid(form)


class MessageDeleteView(OwnerFilteredMixin, OwnerOnlyMutationMixin, DeleteView):
    """Удаление только своего сообщения (или суперпользователь)."""

    model = Message
    template_name = "messages_app/message_confirm_delete.html"
    success_url = reverse_lazy("messages_app:message_list")
    template_name = "messages_app/message_confirm_delete.html"
    success_url = reverse_lazy("messages_app:message_list")

    def delete(self, request, *args, **kwargs):
        """Обрабатывает успешное удаление сообщения.
        Добавляет уведомление об удалении и вызывает стандартный метод DeleteView.
        Args:
            request (HttpRequest): Объект запроса.
            *args, **kwargs: Дополнительные аргументы маршрута.
        Returns:
            HttpResponseRedirect: Перенаправление на страницу списка сообщений."""
        messages.success(self.request, "Сообщение удалено.")
        return super().delete(request, *args, **kwargs)
