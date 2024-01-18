
function saveFormData() {
    // Retrieve form data
    var formData = {};
    var formElements = document.forms[0].elements;
    for (var i = 0; i < formElements.length; i++) {
        formData[formElements[i].name] = formElements[i].value;
    }

    // Store form data in localStorage
    localStorage.setItem('formData', JSON.stringify(formData));
}

