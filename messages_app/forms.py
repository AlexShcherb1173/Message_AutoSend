from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    """Форма для создания и редактирования сообщений, используемых в рассылках.
    Используется для модели Message и предоставляет удобный интерфейс
    для ввода темы и текста письма.
    Особенности:
        • Текст письма (body) отображается в многострочном Textarea.
        • Выполняется валидация темы (subject) — минимум 3 символа."""

    class Meta:
        """Метаданные формы MessageForm.
        Определяет:
            - модель Message, с которой связана форма;
            - редактируемые поля (subject, body);
            - пользовательский виджет для поля body.        """
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_subject(self) -> str:
        """Проверяет корректность введённой темы письма.
        Тема должна содержать не менее 3 символов и не состоять только из пробелов.
        Raises:
            forms.ValidationError: если тема слишком короткая.
        Returns:
            str: Очищенная и обрезанная тема письма."""
        s = (self.cleaned_data.get("subject") or "").strip()
        if len(s) < 3:
            raise forms.ValidationError("Тема должна быть не короче 3 символов.")
        return s