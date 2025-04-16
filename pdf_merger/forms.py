from django import forms

class PDFMergeForm(forms.Form):
    pdf_files = forms.FileField(widget=forms.FileInput(attrs={'multiple': True}), required=True)
