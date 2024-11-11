// script.js
$(document).ready(function() {
    // Handle click event for dropdown category
    $('.dropdown-catagory').on('click', function(event) {
        event.preventDefault(); // Prevent the default action

        var $this = $(this);
        var $dropdownMenu = $this.next('.dropdown-menu');

        // Toggle the visibility of the dropdown menu
        $dropdownMenu.slideToggle('fast');

        // Hide other open dropdowns
        $('.dropdown-menu').not($dropdownMenu).slideUp('fast');
    });

    // Close dropdown if clicked outside
    $(document).click(function(event) {
        if (!$(event.target).closest('.dropdown-menu, .dropdown-catagory').length) {
            $('.dropdown-menu').slideUp('fast');
        }
    });
});
