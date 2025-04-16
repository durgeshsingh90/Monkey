from django import forms

class LogUploadForm(forms.Form):
    file = forms.FileField(required=False)
    log_data = forms.CharField(widget=forms.Textarea, required=False)
