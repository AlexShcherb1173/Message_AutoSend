from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.http import HttpRequest


def build_activation_link(request: HttpRequest, user) -> str:
    """Формирует абсолютную ссылку вида:
    https://<host>/users/activate/<uidb64>/<token>/"""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("users:activate", kwargs={"uidb64": uidb64, "token": token})
    return request.build_absolute_uri(path)
