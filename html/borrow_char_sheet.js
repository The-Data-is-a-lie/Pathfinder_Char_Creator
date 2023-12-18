function createDropdownMenuAndExtraBoxes(dropdownId, numExtraBoxesId, tableId) {
  const dropdownMenu = document.getElementById(dropdownId);
  const numExtraBoxes = document.getElementById(numExtraBoxesId);
  const table = document.getElementById(tableId);

  dropdownMenu.addEventListener('change', () => {
    const selectedValue = parseInt(dropdownMenu.value);
    numExtraBoxes.value = selectedValue;
    createExtraBoxes(table, selectedValue);
  });

  function createExtraBoxes(container, numExtraBoxes) {
    // Clear the previous extra boxes
    container.innerHTML = '';

    for (let i = 0; i < numExtraBoxes; i++) {
      const inputBox = document.createElement('input');
      inputBox.type = 'text';
      inputBox.name = `${tableId}-extra-box-${i}`;
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
  createExtraBoxes(table, initialSelectedValue);
}

// Function for the Feats section
createDropdownMenuAndExtraBoxes('feats-dropdown-menu', 'feats-numExtraBoxes', 'feats-table');

// Function for the Equipment section
createDropdownMenuAndExtraBoxes('equipment-dropdown-menu', 'equipment-numExtraBoxes', 'equipment-table');

// Function for the Class Features section
createDropdownMenuAndExtraBoxes('features-menu', 'features-numExtraBoxes', 'features-table');

// Function for the path-of-war section
createDropdownMenuAndExtraBoxes('path-of-war-dropdown-menu', 'path-of-war-numExtraBoxes', 'path-of-war-table');

// Function for the path-of-war section
createDropdownMenuAndExtraBoxes('attack-dropdown-menu', 'attack-numExtraBoxes', 'attack-table');


