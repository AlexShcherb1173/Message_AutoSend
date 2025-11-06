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
from django.contrib import messages
from .models import Recipient
from .forms import RecipientForm


class RecipientListView(ListView):
    """Представление для отображения списка получателей.
    Отображает все объекты модели Recipient с пагинацией.
    Используется шаблон `clients/recipient_list.html`.
    Атрибуты:
        model (Model): Модель, с которой работает представление.
        template_name (str): Путь к HTML-шаблону.
        context_object_name (str): Имя переменной в шаблоне для списка объектов.
        paginate_by (int): Количество элементов на одной странице."""
    model = Recipient
    template_name = "clients/recipient_list.html"
    context_object_name = "recipients"
    paginate_by = 10


class RecipientDetailView(DetailView):
    """Представление для просмотра деталей одного получателя.
    Отображает полную информацию об объекте Recipient.
    Используется шаблон `clients/recipient_detail.html`.
    Атрибуты:
        model (Model): Модель получателя.
        template_name (str): Шаблон страницы деталей.
        context_object_name (str): Имя переменной в шаблоне."""
    model = Recipient
    template_name = "clients/recipient_detail.html"
    context_object_name = "recipient"


class RecipientCreateView(CreateView):
    """Представление для создания нового получателя.
    Отображает форму добавления получателя и обрабатывает её отправку.
    При успешном добавлении отображает сообщение и перенаправляет
    на список получателей.
    Атрибуты:
        model (Model): Модель получателя.
        form_class (Form): Форма создания объекта.
        template_name (str): Шаблон формы.
        success_url (str): URL для перенаправления после успешного создания."""
    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        """Обрабатывает успешную валидацию формы.
        Добавляет уведомление о создании получателя и вызывает
        стандартное поведение родительского класса.
        Args:
            form (RecipientForm): Валидная форма получателя.
        Returns:
            HttpResponse: Ответ с редиректом на страницу успеха."""
        messages.success(self.request, "Получатель успешно добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(UpdateView):
    """Представление для редактирования данных существующего получателя.
    Позволяет изменить поля объекта Recipient и сохраняет изменения.
    После успешного редактирования показывает сообщение и перенаправляет
    на список получателей."""
    model = Recipient
    form_class = RecipientForm
    template_name = "clients/recipient_form.html"
    success_url = reverse_lazy("clients:recipient_list")

    def form_valid(self, form):
        """Обрабатывает успешное обновление данных получателя.
            Args:
            form (RecipientForm): Валидная форма с изменёнными данными.
        Returns:
            HttpResponse: Ответ с редиректом на страницу списка."""
        messages.success(self.request, "Данные получателя обновлены.")
        return super().form_valid(form)


class RecipientDeleteView(DeleteView):
    """Представление для удаления получателя.
    Запрашивает подтверждение удаления, а после успешного удаления
    отображает уведомление и перенаправляет на список получателей."""
    model = Recipient
    template_name = "clients/recipient_confirm_delete.html"
    success_url = reverse_lazy("clients:recipient_list")

    def delete(self, request, *args, **kwargs):
        """Обрабатывает удаление объекта Recipient.
        Добавляет уведомление об успешном удалении перед вызовом
        стандартного метода удаления.
        Args:
            request (HttpRequest): Объект запроса.
            *args, **kwargs: Дополнительные параметры.
        Returns:
            HttpResponseRedirect: Перенаправление на страницу списка получателей."""
        messages.success(self.request, "Получатель удалён.")
        return super().delete(request, *args, **kwargs)
