import webbrowser
# Specify the path to the Chrome executable
chrome_executable_path = '/path/to/chrome/executable'

# Register Chrome with Python
webbrowser.register('chrome', chrome_executable_path)

# Specify the path to your HTML file
html_file_path = 'character_info_123455678910.html'

# Get a reference to the Chrome webbrowser
chrome_browser = webbrowser.get('chrome')

# Open the HTML file in the Chrome webbrowser
chrome_browser.open(html_file_path)