import fillpdf
from fillpdf import fillpdfs

#set up
#below example works with the dictionary
path = 'output.pdf'
# data_dict = fillpdfs.get_form_fields(path)
limited_data_dict = {}
limit = 100
# # Limit the number of entries
# limit = 30


# Everything needed to run in this section
#importing necessary libraries
import fillpdf        
from fillpdf import fillpdfs


def limit_function():
    path = 'output.pdf'
    original_data_dict = fillpdfs.get_form_fields(path)
    # Create a new dictionary to store the limited entries
    limited_data_dict = {}
    # Limit the number of entries
    limit = 100
    # Copy the first 50 entries from the original data_dict to the limited_data_dict
    for key, value in original_data_dict.items():
        if limit == 0:
            break  # Stop copying after N entries
        limited_data_dict[key] = value
        limit -= 1
        
def replace_function(data_dict):
    for key, value in data_dict.items():
        if value is None:
            data_dict[key] = 'LOL'
        elif isinstance(value, str):
            if value == "" or value == '-5' or value == '0' or (hasattr(value, '__len__') and len(value) == 0):
              data_dict[key] = 50
        elif isinstance(value, (int, float)):  # Check if value is numerical
            data_dict[key] = 'LOL'
        elif isinstance(value, dict):
            replace_function(value)


limit_function()
#replace_none_and_blank_with_bbox(data_dict)
replace_function(limited_data_dict)
fillpdfs.write_fillable_pdf(path, 'dnd_char.pdf', limited_data_dict)

    # Now, data_dict will have None and blank values replaced with 0
#print(data_dict)