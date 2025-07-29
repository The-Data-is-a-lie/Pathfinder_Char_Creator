def modded_char_sheet_func(modded_char_sheet):
    if not isinstance(modded_char_sheet, str):
        print("modded_char_sheet is not a string")
        return False
    
    if modded_char_sheet.lower() in ['y', 'yes', 'true']:
        print("modded_char_sheet THIS IS STRING")
        return True
    
    return False
