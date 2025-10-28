from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Message
from .forms import MessageForm


class MessageListView(ListView):
    model = Message
    template_name = "messages_app/message_list.html"
    context_object_name = "messages_list"
    paginate_by = 10


class MessageDetailView(DetailView):
    model = Message
    template_name = "messages_app/message_detail.html"
    context_object_name = "message"


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        messages.success(self.request, "Сообщение создано.")
        return super().form_valid(form)


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "messages_app/message_form.html"
    success_url = reverse_lazy("messages_app:message_list")

    def form_valid(self, form):
        messages.success(self.request, "Сообщение обновлено.")
        return super().form_valid(form)


class MessageDeleteView(DeleteView):
    model = Message
    template_name = "messages_app/message_confirm_delete.html"
    success_url = reverse_lazy("messages_app:message_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Сообщение удалено.")
        return super().delete(request, *args, **kwargs)
