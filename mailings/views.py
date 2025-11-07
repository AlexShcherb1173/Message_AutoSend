from __future__ import annotations

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Count

from .forms import MailingForm
from .models import Mailing, MailingStatus
from .services import send_mailing
from clients.models import Recipient


class MailingListView(ListView):
    """
    Представление списка рассылок.

    Отображает все объекты модели Mailing с пагинацией и
    поддержкой фильтрации по статусу через GET-параметр `status`.

    Пример: /mailings/?status=Запущена

    Атрибуты:
        model (Model): Модель рассылки.
        paginate_by (int): Количество элементов на странице.
        template_name (str): Шаблон для отображения списка.
        context_object_name (str): Имя переменной в контексте шаблона.
    """

    model = Mailing
    paginate_by = 20
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        """
        Возвращает QuerySet рассылок, опционально фильтруя по статусу.

        Returns:
            QuerySet: Список рассылок (возможно отфильтрованный).
        """
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class MailingDetailView(DetailView):
    """Представление для просмотра подробной информации о рассылке.
    Атрибуты:
        model (Model): Модель рассылки.
        template_name (str): Шаблон страницы деталей.
        context_object_name (str): Имя переменной в контексте."""

    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"


class MailingCreateView(CreateView):
    """Представление для создания новой рассылки.
    После успешного сохранения пересчитывает статус,
    чтобы гарантировать корректное начальное состояние."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        """Обрабатывает успешную валидацию формы.
        Пересчитывает статус рассылки (refresh_status) после сохранения.
        Args:
            form (MailingForm): Валидная форма.
        Returns:
            HttpResponseRedirect: Перенаправление на success_url."""
        response = super().form_valid(form)
        self.object.refresh_status(save=True)
        return response


class MailingUpdateView(UpdateView):
    """Представление для редактирования существующей рассылки.
    После обновления формы пересчитывает статус с учётом новых дат."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        """Обрабатывает успешное обновление данных рассылки.
            Args:
            form (MailingForm): Валидная форма с изменёнными полями.
        Returns:
            HttpResponseRedirect: Перенаправление на success_url."""
        response = super().form_valid(form)
        self.object.refresh_status(save=True)
        return response


class MailingDeleteView(DeleteView):
    """Представление для удаления рассылки.
    Отображает страницу подтверждения удаления и после подтверждения
    удаляет объект, перенаправляя на список рассылок."""

    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:list")


class MailingSendView(View):
    """Представление для ручного запуска рассылки из пользовательского интерфейса.
    Работает только с POST-запросами.
    Использует сервис send_mailing() для фактической отправки
    (или симуляции — dry-run).
    POST-параметры:
        dry_run (str): Если "1", выполняется имитация отправки без реальных писем."""

    def post(self, request, pk: int):
        """Обрабатывает POST-запрос на запуск рассылки.
        Args:
            request (HttpRequest): Запрос от клиента.
            pk (int): ID рассылки, которую нужно отправить.
        Returns:
            HttpResponseRedirect: Перенаправление на страницу деталей рассылки."""
        mailing = get_object_or_404(Mailing, pk=pk)
        dry_run = request.POST.get("dry_run") == "1"
        result = send_mailing(mailing, user=request.user, dry_run=dry_run)

        if dry_run:
            messages.info(
                request,
                f"DRY-RUN: получателей={result.total}, бы отправили={result.total}, реально отправлено=0.",
            )
        else:
            messages.success(
                request,
                f"Готово: всего={result.total}, отправлено={result.sent}, пропущено/ошибок={result.skipped}.",
            )
        return redirect("mailings:detail", pk=mailing.pk)


class HomeView(TemplateView):
    """Главная страница приложения.
    Отображает агрегированные показатели:
        - общее количество рассылок;
        - количество активных рассылок (со статусом 'Запущена');
        - количество уникальных получателей, участвующих в рассылках."""

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        """Добавляет в контекст сводные статистические данные по рассылкам и получателям.
        Returns:
            dict: Контекст с полями total_mailings, active_mailings, unique_recipients."""
        ctx = super().get_context_data(**kwargs)

        total_mailings = Mailing.objects.count()
        active_mailings = Mailing.objects.filter(status=MailingStatus.RUNNING).count()

        # Уникальные получатели, участвующие хотя бы в одной рассылке
        unique_recipients = Recipient.objects.filter(mailings__isnull=False).distinct().count()

        ctx.update(
            total_mailings=total_mailings,
            active_mailings=active_mailings,
            unique_recipients=unique_recipients,
        )
        return ctx

@require_POST
@login_required  # убери, если проект без аутентификации
def mailing_send(request, pk: int):
    """
    Ручной запуск рассылки из UI.
    Принимает POST с опциональным чекбоксом 'dry_run'.

    Поведение:
      - dry-run: симулирует отправку, ничего реально не шлёт.
      - normal: отправляет письма и пишет логи/attempts.
    По завершении показывает флеш-сообщение и редиректит на detail.
    """
    mailing = get_object_or_404(Mailing, pk=pk)
    dry_run = bool(request.POST.get("dry_run"))

    # user передаём для аудита в логах/attempts (если сервис это поддерживает)
    result = send_mailing(mailing, user=request.user, dry_run=dry_run)

    # обновим статус «по факту»
    mailing.refresh_status(save=True)

    if dry_run:
        messages.info(
            request,
            f"Тестовый запуск завершён: всего адресатов={result.total}, "
            f"реальных отправок не производилось."
        )
    else:
        messages.success(
            request,
            f"Рассылка отправлена: всего={result.total}, "
            f"успешно={result.sent}, пропущено/ошибок={result.skipped}."
        )

    return redirect("mailings:detail", pk=mailing.pk)