// Check if there is stored form data and populate the form
window.onload = function () {
    var storedData = localStorage.getItem('formData');
    if (storedData) {
        var formData = JSON.parse(storedData);
        var formElements = document.forms[0].elements;
        for (var i = 0; i < formElements.length; i++) {
            var fieldName = formElements[i].name;
            if (formData[fieldName]) {
                formElements[i].value = formData[fieldName];
            }
        }
    }
};