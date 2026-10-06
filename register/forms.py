from django import forms

from .models import Booth, EventSession, FloorMap


class EventSessionForm(forms.ModelForm):
    class Meta:
        model = EventSession
        exclude = ("campaign", "created_at", "updated_at")
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "speaker_info": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, campaign=None, **kwargs):
        self.campaign = campaign
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        event_date = cleaned.get("event_date")
        start_time = cleaned.get("start_time")
        end_time = cleaned.get("end_time")
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "End time must be after start time.")
        capacity = cleaned.get("capacity")
        if capacity is not None and capacity < 1:
            self.add_error("capacity", "Capacity must be at least 1, or leave it blank for unlimited.")
        if (self.instance.pk and capacity is not None
                and capacity < self.instance.booked_count):
            self.add_error("capacity", "Capacity cannot be lower than the current booked count.")
        if event_date and self.campaign:
            if event_date < self.campaign.start_date.date() or event_date > self.campaign.end_date.date():
                self.add_error("event_date", "Session date must fall within the event dates.")
        return cleaned


class FloorMapForm(forms.ModelForm):
    class Meta:
        model = FloorMap
        exclude = ("campaign", "created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["image"].required = False

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image and not self.instance.pk:
            raise forms.ValidationError("Choose a floor map image.")
        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Floor map image must be under 10 MB.")
        content_type = getattr(image, "content_type", None) if image else None
        if content_type and not content_type.startswith("image/"):
            raise forms.ValidationError("Upload an image file for the floor map.")
        return image


class BoothForm(forms.ModelForm):
    class Meta:
        model = Booth
        exclude = ("created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["floor_map"].queryset = FloorMap.objects.filter(campaign=campaign)

    def clean(self):
        cleaned = super().clean()
        floor_map = cleaned.get("floor_map")
        for field in ("x_percent", "y_percent"):
            value = cleaned.get(field)
            if value is not None and not 0 <= value <= 100:
                self.add_error(field, "Position must be between 0 and 100 percent.")
        for field in ("width_percent", "height_percent"):
            value = cleaned.get(field)
            if value is not None and not 0 < value <= 100:
                self.add_error(field, "Size must be greater than 0 and at most 100 percent.")
        x, y = cleaned.get("x_percent"), cleaned.get("y_percent")
        width, height = cleaned.get("width_percent"), cleaned.get("height_percent")
        if x is not None and width is not None and x + width > 100:
            self.add_error("width_percent", "Booth must fit within the right edge of the map.")
        if y is not None and height is not None and y + height > 100:
            self.add_error("height_percent", "Booth must fit within the bottom edge of the map.")
        return cleaned
