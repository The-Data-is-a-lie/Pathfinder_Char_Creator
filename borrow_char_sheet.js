function createDropdownMenuAndExtraBoxes() {
    const dropdownMenu = document.getElementById('dropdown-menu');
    const numExtraBoxes = document.getElementById('numExtraBoxes');
    const featsTable = document.getElementById('feats-table');
  
    dropdownMenu.addEventListener('change', () => {
      const selectedValue = parseInt(dropdownMenu.value);
      numExtraBoxes.value = selectedValue;
      createExtraBoxes(featsTable, selectedValue);
    });
  
    function createExtraBoxes(container, numExtraBoxes) {
      // Clear the previous extra boxes
      container.innerHTML = '';
  
      for (let i = 0; i < numExtraBoxes; i++) {
        const inputBox = document.createElement('input');
        inputBox.type = 'text';
        inputBox.name = `Feats-extra-box-${i}`;
        container.appendChild(inputBox);
      }
    }
  
    // Populate the dropdown menu with options
    for (let i = 1; i <= 200; i++) {
      const option = document.createElement('option');
      option.value = i;
      option.textContent = i;
      dropdownMenu.appendChild(option);
    }
  
    // Initialize with the default selected value
    const initialSelectedValue = parseInt(dropdownMenu.value);
    numExtraBoxes.value = initialSelectedValue;
    createExtraBoxes(featsTable, initialSelectedValue);
  }
  
  createDropdownMenuAndExtraBoxes();
  
  