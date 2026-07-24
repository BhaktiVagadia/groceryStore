import re
import requests
from django import forms
from cart_address.models import STATES_CHOICES, COUNTRY_CHOICES


class OrderCheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=150, required=True)
    billing_address_1 = forms.CharField(max_length=255, required=True)
    billing_address_2 = forms.CharField(max_length=255, required=False)
    billing_city = forms.CharField(max_length=100, required=True)
    billing_state = forms.ChoiceField(choices=STATES_CHOICES, required=True)
    billing_country = forms.ChoiceField(choices=COUNTRY_CHOICES, initial='India', required=True)
    billing_zip_code = forms.CharField(max_length=20, required=True)
    mo_no = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=True)

    is_ship_diff = forms.BooleanField(required=False)

    shipping_address_1 = forms.CharField(max_length=255, required=False)
    shipping_address_2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=False)
    shipping_state = forms.ChoiceField(choices=STATES_CHOICES, required=False)
    shipping_country = forms.ChoiceField(choices=COUNTRY_CHOICES, initial='India', required=False)
    shipping_zip_code = forms.CharField(max_length=20, required=False)

    def clean_billing_zip_code(self):
        zip_code = self.cleaned_data.get('billing_zip_code', '').strip()
        return self._validate_pincode_format(zip_code, required=True)

    def clean_shipping_zip_code(self):
        zip_code = self.cleaned_data.get('shipping_zip_code', '').strip()
        return self._validate_pincode_format(zip_code, required=False)

    def clean_mo_no(self):
        mobile = self.cleaned_data.get('mo_no', '').strip()
        if not re.match(r'^[6-9]\d{9}$', mobile):
            raise forms.ValidationError("Enter a valid mobile number.")
        return mobile

    def _validate_pincode_format(self, zip_code, required):
        if not zip_code:
            if required:
                raise forms.ValidationError("This field is required.")
            return zip_code
        if not zip_code.isdigit() or len(zip_code) != 6:
            raise forms.ValidationError('Enter a valid 6-digit PIN code.')
        return zip_code

    def _lookup_pincode(self, zip_code):
        """Returns list of PostOffice dicts for a PIN, [] if not found, None if API unreachable."""
        try:
            response = requests.get(
                f'https://api.postalpincode.in/pincode/{zip_code}',
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            data = response.json()
            if data[0].get('Status') == 'Success':
                return data[0].get('PostOffice') or []
            return []
        except requests.RequestException:
            return None

    def _check_address_matches_pincode(self, zip_code, city, state, zip_field, city_field, state_field):
        if not zip_code or len(zip_code) != 6 or not zip_code.isdigit():
            return  # format errors already raised on the field itself

        post_offices = self._lookup_pincode(zip_code)

        if post_offices is None:
            return  # API unreachable — don't block checkout on a network issue

        if not post_offices:
            self.add_error(zip_field, 'This PIN code does not exist. Please check and re-enter.')
            return

        valid_districts = {po.get('District', '').strip().lower() for po in post_offices}
        valid_names = {po.get('Name', '').strip().lower() for po in post_offices}
        valid_states = {po.get('State', '').strip().lower() for po in post_offices}

        if city and city.strip().lower() not in valid_districts and city.strip().lower() not in valid_names:
            district_list = ', '.join(sorted({po.get('District', '') for po in post_offices}))
            self.add_error(
                city_field,
                f'This city does not match the PIN code entered. Expected: {district_list}.'
            )

        if state and state.strip().lower() not in valid_states:
            state_list = ', '.join(sorted({po.get('State', '') for po in post_offices}))
            self.add_error(
                state_field,
                f'This state does not match the PIN code entered. Expected: {state_list}.'
            )

    def clean(self):
        cleaned_data = super().clean()
        is_ship_diff = cleaned_data.get('is_ship_diff')

        self._check_address_matches_pincode(
            cleaned_data.get('billing_zip_code'),
            cleaned_data.get('billing_city'),
            cleaned_data.get('billing_state'),
            'billing_zip_code', 'billing_city', 'billing_state'
        )

        if is_ship_diff:
            required_shipping_fields = [
                'shipping_address_1', 'shipping_city',
                'shipping_state', 'shipping_country', 'shipping_zip_code'
            ]
            for field in required_shipping_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, forms.ValidationError("This field is required for shipping."))

            self._check_address_matches_pincode(
                cleaned_data.get('shipping_zip_code'),
                cleaned_data.get('shipping_city'),
                cleaned_data.get('shipping_state'),
                'shipping_zip_code', 'shipping_city', 'shipping_state'
            )

        return cleaned_data