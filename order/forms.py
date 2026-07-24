from django import forms

class TrackOrderForm(forms.Form):
    order_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. INV-1024'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'e.g. guest@example.com'})
    )
