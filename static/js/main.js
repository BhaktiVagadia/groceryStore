(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner(0);
    
    
    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 45) {
            $('.nav-bar').addClass('sticky-top shadow-sm');
        } else {
            $('.nav-bar').removeClass('sticky-top shadow-sm');
        }
    });


    // Hero Header carousel
    $(".header-carousel").owlCarousel({
        items: 1,
        autoplay: true,
        smartSpeed: 2000,
        center: false,
        dots: false,
        loop: true,
        margin: 0,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ]
    });


    // ProductList carousel
    $(".productList-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 2000,
        dots: false,
        loop: true,
        margin: 25,
        nav : true,
        navText : [
            '<i class="fas fa-chevron-left"></i>',
            '<i class="fas fa-chevron-right"></i>'
        ],
        responsiveClass: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:2
            },
            1200:{
                items:3
            }
        }
    });

    // ProductList categories carousel
    $(".productImg-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        dots: false,
        loop: true,
        items: 1,
        margin: 25,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ]
    });


    // Single Products carousel
    $(".single-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        dots: true,
        dotsData: true,
        loop: true,
        items: 1,
        nav : true,
        navText : [
            '<i class="bi bi-arrow-left"></i>',
            '<i class="bi bi-arrow-right"></i>'
        ]
    });


    // ProductList carousel
    $(".related-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        dots: false,
        loop: true,
        margin: 25,
        nav : true,
        navText : [
            '<i class="fas fa-chevron-left"></i>',
            '<i class="fas fa-chevron-right"></i>'
        ],
        responsiveClass: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            },
            1200:{
                items:4
            }
        }
    });



    // Product Quantity
    $('.quantity button').on('click', function () {
        var button = $(this);
        var oldValue = button.parent().parent().find('input').val();
        if (button.hasClass('btn-plus')) {
            var newVal = parseFloat(oldValue) + 1;
        } else {
            if (oldValue > 0) {
                var newVal = parseFloat(oldValue) - 1;
            } else {
                newVal = 0;
            }
        }
        button.parent().parent().find('input').val(newVal);

        let $row = button.closest('tr');
        let productId = $row.data('product-id');
        let variantId = $row.data('variant-id');
        if(button.hasClass('cart-item')){
            $.ajax({
                url: `/cart/addToCart/${productId}/`,
                type: 'GET',
                data: { 'quantity': newVal, 'variant_id': variantId || '' },
                dataType: 'json',
                success: function(data) {
                    if (data.status === 'success') {
                        $row.find('.row-total-val').text(parseFloat(data.item_total_price).toFixed(2));
                        $('.cart-row-total').text(parseFloat(data.row_total).toFixed(2));
                        $('.cart-total').text(parseFloat(data.cart_total).toFixed(2));
                        $('.shipping-amount').text(parseFloat(data.shipping_amount).toFixed(2));
                        $('.tax-amount').text(parseFloat(data.tax_amount).toFixed(2));
                        $('.discount-amount').text(parseFloat(data.discount_amount).toFixed(2));
                    }
                }
            });
        }
    });
    // Handle manual typing inputs
    $(document).on('change', '.quantity-input', function () {
        var input = $(this);
        var newVal = parseInt(input.val());

        // Validate input values securely
        if (isNaN(newVal) || newVal < 1) {
            newVal = 1;
            input.val(newVal);
        }

        var $row = input.closest('tr');
        var productId = $row.data('product-id');
        var variantId = $row.data('variant-id');
        if(input.hasClass('cart-item')){
            $.ajax({
                url: `/cart/addToCart/${productId}/`,
                type: 'GET',
                data: { 'quantity': newVal, 'variant_id': variantId || '' },
                dataType: 'json',
                success: function (data) {
                    if (data.status === 'success') {
                        $row.find('.row-total-val').text(parseFloat(data.item_total_price).toFixed(2));
                        $('.cart-row-total').text(parseFloat(data.row_total).toFixed(2));
                        $('.cart-total').text(parseFloat(data.cart_total).toFixed(2));
                        $('.shipping-amount').text(parseFloat(data.shipping_amount).toFixed(2));
                        $('.tax-amount').text(parseFloat(data.tax_amount).toFixed(2));
                        $('.discount-amount').text(parseFloat(data.discount_amount).toFixed(2));
                    }
                },
                error: function (xhr) {
                    console.error("AJAX Error updating manual quantity input.");
                }
            });
        }
    });



   // Back to top button
   $(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
        $('.back-to-top').fadeIn('slow');
    } else {
        $('.back-to-top').fadeOut('slow');
    }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });



})(jQuery);