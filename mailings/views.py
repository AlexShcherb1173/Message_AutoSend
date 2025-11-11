from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .forms import MailingForm
from .models import Mailing, MailingStatus, MailingLog, MailingAttempt, AttemptStatus
from .services import send_mailing
from common.mixins import ClientCacheMixin


# ===== Миксины ограничения доступа (владельцы/менеджеры) =====


class OwnerFilteredQuerysetMixin(LoginRequiredMixin):
    """Ограничивает queryset объектами текущего пользователя.
    Если у пользователя есть perm 'mailings.view_all_mailings' — он видит все."""

    view_all_permission = "mailings.view_all_mailings"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.has_perm(self.view_all_permission) or user.is_superuser:
            return qs
        return qs.filter(owner=user)


class OwnerOnlyMutationMixin(UserPassesTestMixin):
    """Разрешает изменение/удаление только владельцу (или суперпользователю).
    Менеджер видит всё, но менять/удалять чужое не может."""

    def test_func(self):
        obj = self.get_object()
        u = self.request.user
        return u.is_superuser or (obj.owner_id == u.id)


# ===== CRUD + отчёты =====


class MailingListView(OwnerFilteredQuerysetMixin, ListView):
    """Список рассылок с фильтрацией по владельцу/статусу и аннотациями статистики."""

    model = Mailing
    paginate_by = 20
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        qs = super().get_queryset().with_stats()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.select_related("message").prefetch_related("recipients")


class MailingDetailView(OwnerFilteredQuerysetMixin, DetailView):
    """Детали рассылки (только для владельца/менеджера/суперадмина) + словарь stats."""

    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        return super().get_queryset().with_stats()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stats"] = self.object.stats_dict()
        return ctx


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание рассылки: владелец = текущий пользователь."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user  # <— записываем владельца
        obj.save()
        form.save_m2m()
        obj.refresh_status(save=True)
        return redirect(self.success_url)


class MailingUpdateView(OwnerFilteredQuerysetMixin, OwnerOnlyMutationMixin, UpdateView):
    """Редактирование только своей рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        resp = super().form_valid(form)
        self.object.refresh_status(save=True)
        return resp


class MailingDeleteView(OwnerFilteredQuerysetMixin, OwnerOnlyMutationMixin, DeleteView):
    """Удаление только своей рассылки."""

    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:list")


class MailingSendView(OwnerFilteredQuerysetMixin, OwnerOnlyMutationMixin, View):
    """Ручной запуск рассылки (POST). Доступно только владельцу (или суперпользователю).
    Менеджер видит карточку, но не отправляет."""

    def post(self, request, pk: int):
        mailing = get_object_or_404(Mailing, pk=pk)
        # OwnerOnlyMutationMixin защитит от чужих действий
        dry_run = request.POST.get("dry_run") == "1"
        result = send_mailing(mailing, user=request.user, dry_run=dry_run)
        mailing.refresh_status(save=True)
        if dry_run:
            messages.info(
                request,
                f"DRY-RUN: всего={result.total}, отправлено=0, пропущено={result.skipped}.",
            )
        else:
            messages.success(
                request,
                f"Готово: всего={result.total}, отправлено={result.sent}, пропущено={result.skipped}.",
            )
        return redirect("mailings:detail", pk=mailing.pk)


class MailingStatsView(OwnerFilteredQuerysetMixin, TemplateView):
    """Страница отчётов.
    Пользователь видит только свои данные, менеджер/суперадмин — сводку по всем."""

    template_name = "mailings/mailing_stats.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        mailings_qs = Mailing.objects.all()
        attempts_qs = MailingAttempt.objects.all()

        if not (user.has_perm("mailings.view_all_mailings") or user.is_superuser):
            mailings_qs = mailings_qs.filter(owner=user)
            attempts_qs = attempts_qs.filter(mailing__owner=user)

        total_mailings = mailings_qs.count()
        attempts_total = attempts_qs.count()
        attempts_ok = attempts_qs.filter(status=AttemptStatus.SUCCESS).count()
        attempts_fail = attempts_qs.filter(status=AttemptStatus.FAIL).count()

        ctx.update(
            total_mailings=total_mailings,
            attempts_total=attempts_total,
            attempts_ok=attempts_ok,
            attempts_fail=attempts_fail,
        )

        # Дополнительно (как в stats шаблоне): построчная статистика по рассылкам
        mailings = (
            mailings_qs.annotate(
                sent_total=Count("logs", filter=Q(logs__status="SENT")),
                failed_total=Count("logs", filter=Q(logs__status="ERROR")),
                attempt_ok_total=Count(
                    "attempts", filter=Q(attempts__status=AttemptStatus.SUCCESS)
                ),
                attempt_fail_total=Count(
                    "attempts", filter=Q(attempts__status=AttemptStatus.FAIL)
                ),
            )
            .select_related("message")
            .prefetch_related("recipients")
        )
        ctx["mailings"] = mailings
        return ctx


# Доп. функционал для менеджеров: «отключить» рассылку (права required)
class MailingDisableView(PermissionRequiredMixin, View):
    """Принудительно завершить рассылку (для менеджеров/админов).
    Требуется perm: 'mailings.disable_mailing'."""

    permission_required = "mailings.disable_mailing"

    def post(self, request, pk: int):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = MailingStatus.FINISHED
        mailing.save(update_fields=["status", "updated_at"])
        messages.warning(request, f"Рассылка #{mailing.pk} принудительно завершена.")
        return redirect("mailings:detail", pk=mailing.pk)


# Вспомогательная функция (если используешь ручной POST-эндпойнт)
@require_POST
@login_required
def mailing_send(request, pk: int):
    mailing = get_object_or_404(Mailing, pk=pk)
    if mailing.owner_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Вы не можете отправлять чужую рассылку.")
        return redirect("mailings:detail", pk=mailing.pk)
    dry_run = bool(request.POST.get("dry_run"))
    result = send_mailing(mailing, user=request.user, dry_run=dry_run)
    mailing.refresh_status(save=True)
    if dry_run:
        messages.info(
            request,
            f"Тестовый запуск завершён: адресатов={result.total}, реальных отправок нет.",
        )
    else:
        messages.success(
            request,
            f"Рассылка отправлена: всего={result.total}, успешно={result.sent}, ошибок={result.skipped}.",
        )
    return redirect("mailings:detail", pk=mailing.pk)


@method_decorator(
    cache_page(60 * 5, key_prefix="mailings:user_report"), name="dispatch"
)
class MailingUserReportView(ClientCacheMixin, TemplateView):
    """Персональный отчёт по рассылкам владельца.
    - По умолчанию показывает отчёт для текущего пользователя.
    - Менеджер/суперпользователь может передать ?user=<id> чтобы смотреть чужие.
    - Серверный кэш: 5 минут (Redis через Django cache).
    - Клиентский кэш: заголовок Cache-Control (по ClientCacheMixin)."""

    template_name = "mailings/user_report.html"
    cache_seconds = 120  # клиентский кэш (браузер) — 2 минуты

    def _target_user(self):
        u = self.request.user
        if u.is_superuser or u.has_perm("mailings.view_all_mailings"):
            user_id = self.request.GET.get("user")
            if user_id:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                target = User.objects.filter(pk=user_id).first()
                if target:
                    return target
        return u

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = self._target_user()
        ctx["target_user"] = target

        # ----- серверный кэш для агрегатов -----
        cache_key = f"mailings:user_report:v1:summary:{target.pk}"
        summary = cache.get(cache_key)

        if summary is None:
            mailings_qs = Mailing.objects.filter(owner=target)
            attempts_qs = MailingAttempt.objects.filter(mailing__owner=target)
            logs_qs = MailingLog.objects.filter(mailing__owner=target)

            # количество уникальных получателей среди всех рассылок пользователя
            recipients_total = mailings_qs.values("recipients").distinct().count()

            summary = {
                "total_mailings": mailings_qs.count(),
                "active_mailings": mailings_qs.filter(
                    status=MailingStatus.RUNNING
                ).count(),
                "finished_mailings": mailings_qs.filter(
                    status=MailingStatus.FINISHED
                ).count(),
                "recipients_total": recipients_total,
                "attempts_total": attempts_qs.count(),
                "attempts_ok": attempts_qs.filter(status=AttemptStatus.SUCCESS).count(),
                "attempts_fail": attempts_qs.filter(status=AttemptStatus.FAIL).count(),
                "sent_total": logs_qs.filter(status="SENT").count(),
                "errors_total": logs_qs.filter(status="ERROR").count(),
            }
            cache.set(cache_key, summary, 300)  # 5 минут

        ctx["summary"] = summary

        # Построчная статистика по рассылкам (кверисет не кладём в Redis — отдаём «живой» QS)
        ctx["mailings"] = (
            Mailing.objects.filter(owner=target)
            .annotate(
                recipients_total=Count("recipients", distinct=True),
                sent_total=Count("logs", filter=Q(logs__status="SENT")),
                failed_total=Count("logs", filter=Q(logs__status="ERROR")),
                attempt_ok_total=Count(
                    "attempts", filter=Q(attempts__status=AttemptStatus.SUCCESS)
                ),
                attempt_fail_total=Count(
                    "attempts", filter=Q(attempts__status=AttemptStatus.FAIL)
                ),
            )
            .select_related("message")
            .prefetch_related("recipients")
        )
        return ctx
