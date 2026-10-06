from django import forms

from .models import (
    Booth, Employer, EventSession, FloorMap, InterviewSlot, Job,
    TrainingProvider, University, UniversityProgram, VoucherPromotion,
)


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


class _EventProfileForm(forms.ModelForm):
    booth_model = None

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.campaign = campaign
        self.fields["booth"].queryset = Booth.objects.filter(floor_map__campaign=campaign)
        if self.instance.pk:
            self.fields["logo"].required = False

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo and logo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Logo must be under 5 MB.")
        return logo

    def clean(self):
        cleaned = super().clean()
        booth = cleaned.get("booth")
        if booth and self.campaign and booth.floor_map.campaign_id != self.campaign.id:
            self.add_error("booth", "Choose a booth belonging to this event.")
        return cleaned


class EmployerForm(_EventProfileForm):
    class Meta:
        model = Employer
        exclude = ("campaign", "created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class UniversityForm(_EventProfileForm):
    class Meta:
        model = University
        exclude = ("campaign", "created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class TrainingProviderForm(_EventProfileForm):
    class Meta:
        model = TrainingProvider
        exclude = ("campaign", "created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        exclude = ("created_at", "updated_at")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "requirements": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employer"].queryset = Employer.objects.filter(campaign=campaign)


class UniversityProgramForm(forms.ModelForm):
    class Meta:
        model = UniversityProgram
        exclude = ("created_at", "updated_at")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "eligibility": forms.Textarea(attrs={"rows": 2}),
            "internship_fresher_info": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["university"].queryset = University.objects.filter(campaign=campaign)


class InterviewSlotForm(forms.ModelForm):
    class Meta:
        model = InterviewSlot
        exclude = ("created_at", "updated_at")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.campaign = campaign
        self.fields["employer"].queryset = Employer.objects.filter(campaign=campaign)

    def clean(self):
        cleaned = super().clean()
        employer = cleaned.get("employer")
        date = cleaned.get("date")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        mode = cleaned.get("booking_mode")
        duration = cleaned.get("slot_duration_minutes")
        capacity = cleaned.get("capacity")
        if capacity is not None and capacity < 1:
            self.add_error("capacity", "Capacity must be at least 1.")
        if start and end and end <= start:
            self.add_error("end_time", "End time must be after start time.")
        if date and self.campaign and not (
            self.campaign.start_date.date() <= date <= self.campaign.end_date.date()
        ):
            self.add_error("date", "Interview date must fall within the event dates.")
        if employer and self.campaign and employer.campaign_id != self.campaign.id:
            self.add_error("employer", "Choose an employer belonging to this event.")
        if mode == InterviewSlot.MODE_OPEN:
            if not duration or duration < 1:
                self.add_error("slot_duration_minutes", "Enter a positive slot duration for open booking.")
            elif start and end:
                duration_minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
                if duration_minutes <= 0 or duration_minutes % duration:
                    self.add_error("slot_duration_minutes", "The availability period must divide evenly into slots.")
        else:
            cleaned["slot_duration_minutes"] = None
        return cleaned


class VoucherPromotionForm(forms.ModelForm):
    class Meta:
        model = VoucherPromotion
        exclude = ("created_at", "updated_at")
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "instructions": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provider"].queryset = TrainingProvider.objects.filter(campaign=campaign)
        if self.instance.pk:
            self.fields["document"].required = False

    def clean_document(self):
        document = self.cleaned_data.get("document")
        if not document:
            return document
        if document.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Promotion document must be under 10 MB.")
        if document.name.rsplit(".", 1)[-1].lower() not in {"pdf", "doc", "docx"}:
            raise forms.ValidationError("Upload a PDF, DOC, or DOCX document.")
        return document
