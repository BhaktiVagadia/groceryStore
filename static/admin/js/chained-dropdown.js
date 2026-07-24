document.addEventListener('DOMContentLoaded', function () {
    const productSelect = document.querySelector('#id_product');
    const variantSelect = document.querySelector('#id_variant');

    if (productSelect && variantSelect) {
        productSelect.addEventListener('change', function () {
            const productId = this.value;

            // Clear existing options except the first blank selection '---------'
            variantSelect.innerHTML = '<option value="">---------</option>';

            if (!productId) return; // Exit if product selection is cleared

            // Send AJAX call to retrieve specific product variants
            fetch(`inventory/ajax/load-variants/?product_id=${productId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(variant => {
                        const option = document.createElement('option');
                        option.value = variant.id;
                        option.textContent = variant.name; // Uses field specified in step 1
                        variantSelect.appendChild(option);
                    });
                })
                .catch(error => console.error('Error loading variants:', error));
        });
    }
});
