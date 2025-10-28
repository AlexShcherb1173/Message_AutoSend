from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
        }

    def clean_subject(self):
        s = (self.cleaned_data.get("subject") or "").strip()
        if len(s) < 3:
            raise forms.ValidationError("Тема должна быть не короче 3 символов.")
        return s