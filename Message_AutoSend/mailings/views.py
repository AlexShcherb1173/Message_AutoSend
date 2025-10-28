from __future__ import annotations

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.db.models import Count

from .forms import MailingForm
from .models import Mailing, MailingStatus
from .services import send_mailing
from clients.models import Recipient


class MailingListView(ListView):
    model = Mailing
    paginate_by = 20
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

class MailingDetailView(DetailView):
    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.refresh_status(save=True)
        return response


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.refresh_status(save=True)
        return response


class MailingDeleteView(DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:list")


class MailingSendView(View):
    """Ручной запуск отправки рассылки из UI. POST-only."""
    def post(self, request, pk: int):
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
    template_name = "index.html"

    def get_context_data(self, **kwargs):
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
