from django.contrib import admin
from product_images.models import ProductImage
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe



class ProductImageInlineFormSet(BaseInlineFormSet):
    def save(self, commit=True):
        instances = super().save(commit=False)

        # Look up which form row prefix was chosen by the radio group
        selected_form_prefix = self.data.get('unique_base_image_radio')

        for form in self.forms:
            if hasattr(form, 'instance') and form.instance:
                # If this row prefix matches the clicked radio value, set True; others become False
                form.instance.is_base = (form.prefix == selected_form_prefix)
                if commit:
                    form.instance.save()

        return instances


# 2. Custom Input widget that forces a raw script load without external assets
class ScriptInjectorWidget(forms.HiddenInput):
    def render(self, name, value, attrs=None, renderer=None):
        hidden_input = super().render(name, value, attrs, renderer)

        # The script is directly bound to the element inside the DOM rendering loop
        radio_transform_script = """
        <script type="text/javascript">
            (function($) {
                function applyRadioUI() {
                    $('.form-row.field-is_base').each(function() {
                        var $row = $(this);
                        var $checkbox = $row.find('input[type="checkbox"]');
                        if ($checkbox.length === 0) return; 

                        var originalName = $checkbox.attr('name');
                        var prefix = originalName.replace('-is_base', '');
                        var isChecked = $checkbox.is(':checked');

                        // Find the theme's flex container wrapper layout
                        var $flexContainer = $row.find('.flex-container.checkbox-row, div > div').first();

                        var radioHtml = '<input type="radio" name="unique_base_image_radio" value="' + prefix + '" ' + (isChecked ? 'checked' : '') + ' style="margin: 4px 8px 0 0; transform: scale(1.3); cursor: pointer;">';
                        var labelHtml = '<label style="cursor: pointer; font-weight: bold; display: inline-block;">Is base</label>';

                        $flexContainer.empty().append(radioHtml).append(labelHtml);
                    });
                }

                $(document).ready(function() {
                    applyRadioUI();
                    $(document).on('formset:added', function() {
                        setTimeout(applyRadioUI, 50); // Small timeout allows Django's dynamic row to mount completely
                    });
                });
            })(django.jQuery);
        </script>
        """
        return mark_safe(hidden_input + radio_transform_script)


# 3. Model Form that injects our script tag safely inside the row layouts
class ProductImageInlineForm(forms.ModelForm):
    # We append an artificial hidden field whose sole job is to safely output our JS string
    script_loader = forms.CharField(widget=ScriptInjectorWidget(), required=False, initial='run')

    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductImageInline(admin.StackedInline):
    model = ProductImage
    form = ProductImageInlineForm
    formset = ProductImageInlineFormSet
    extra = 0