from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label="Your Name",
    )
    email = forms.EmailField(
        label="Email Address",
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={"rows": 6}),
        max_length=4000,
    )

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_message(self):
        return self.cleaned_data["message"].strip()