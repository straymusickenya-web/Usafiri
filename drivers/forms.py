import re
from PIL import Image
from django import forms
from drivers.models import DriverProfile


def parse_destinations(raw_value):
    parts = re.split(r"[\n,]+", raw_value or "")
    cleaned = []
    seen = set()

    for part in parts:
        name = part.strip()
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(name)

    return cleaned


class DriverProfileForm(forms.ModelForm):
    destinations = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Enter one destination per line or separate with commas.\nExample:\nMombasa\nNakuru\nKisumu",
                "class": "w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500",
            }
        ),
        help_text="Add the places this driver is willing to go to.",
    )

    class Meta:
        model = DriverProfile
        fields = ("id_number", "id_photo", "vehicle_type", "vehicle_seats", "location")
        labels = {
            "id_number": "ID number",
            "id_photo": "ID photo",
            "vehicle_type": "Vehicle type",
            "vehicle_seats": "Vehicle seats",
            "location": "Base location",
        }
        help_texts = {
            "location": "Driver base city/neighborhood",
            "id_photo": "Upload a clear photo of your ID (Max 5MB, JPEG/PNG, min 400x400px)",
        }
        widgets = {
            "vehicle_seats": forms.NumberInput(attrs={"min": 1, "max": 50, "value": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["destinations"].initial = "\n".join(
                self.instance.active_destinations().values_list("name", flat=True)
            )

    def clean_id_number(self):
        id_number = self.cleaned_data.get("id_number")
        qs = DriverProfile.objects.filter(id_number=id_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This ID number is already registered.")
        return id_number

    def clean_destinations(self):
        destinations = parse_destinations(self.cleaned_data.get("destinations", ""))

        if not destinations:
            raise forms.ValidationError("Add at least one destination.")

        if len(destinations) > 15:
            raise forms.ValidationError("Please keep destinations to 15 or fewer.")

        return destinations

    def clean_id_photo(self):
        f = self.cleaned_data.get("id_photo")

        if not f:
            if self.instance and self.instance.pk and self.instance.id_photo:
                return self.instance.id_photo
            raise forms.ValidationError("ID photo is required.")

        if hasattr(f, "content_type") and f.content_type not in ("image/jpeg", "image/png"):
            raise forms.ValidationError("Only JPEG/PNG formats are supported.")

        if hasattr(f, "size") and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Maximum file size is 5MB.")

        try:
            image = Image.open(f)
            w, h = image.size
            if w < 400 or h < 400:
                raise forms.ValidationError("Image is too small. Minimum size is 400x400 pixels.")
            f.seek(0)
        except Exception as e:
            if "too small" in str(e):
                raise
            raise forms.ValidationError(f"Invalid image file: {str(e)}")

        return f