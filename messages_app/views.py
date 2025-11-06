from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Message
from .forms import MessageForm


class MessageListView(ListView):
    """Представление списка сообщений.
    Отображает все объекты модели Message с пагинацией.
    Используется для просмотра доступных шаблонов сообщений,
    которые могут быть выбраны при создании рассылки.
    Атрибуты:
        model (Model): Модель сообщений.
        template_name (str): Путь к шаблону для отображения списка.
        context_object_name (str): Имя переменной, доступной в шаблоне.
        paginate_by (int): Количество элементов на одной странице."""

    model = Message
    template_name = "messages_app/message_list.html"
    context_object_name = "messages_list"
    paginate_by = 10


class MessageDetailView(DetailView):
    """Представление деталей сообщения.
    Отображает содержимое одного конкретного сообщения.
    Используется для просмотра темы и текста письма до включения
    его в рассылку."""

    model = Message
    template_name = "messages_app/message_detail.html"
    context_object_name = "message"


class MessageCreateView(CreateView):
    """Представление для создания нового сообщения.
    Использует форму MessageForm, выполняет валидацию полей
    и выводит уведомление об успешном создании через messages framework."""

    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        """Обрабатывает успешное создание сообщения.
        Добавляет уведомление о создании и вызывает стандартное поведение
        базового класса CreateView.
        Args:
            form (MessageForm): Валидная форма с данными нового сообщения.
        Returns:
            HttpResponseRedirect: Перенаправление на список сообщений."""
        messages.success(self.request, "Сообщение создано.")
        return super().form_valid(form)


class MessageUpdateView(UpdateView):
    """Представление для редактирования существующего сообщения.
    Позволяет изменить тему и тело письма, а также сообщает пользователю
    об успешном сохранении изменений."""

    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        """Обрабатывает успешное обновление данных сообщения.
        Добавляет уведомление об обновлении и вызывает родительский метод.
        Args:
            form (MessageForm): Валидная форма с обновлёнными данными.
        Returns:
            HttpResponseRedirect: Перенаправление на страницу списка сообщений."""
        messages.success(self.request, "Сообщение обновлено.")
        return super().form_valid(form)


class MessageDeleteView(DeleteView):
    """    Представление для удаления сообщения.
    Запрашивает подтверждение удаления и после подтверждения
    показывает уведомление об успешном удалении через messages framework."""

    model = Message
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