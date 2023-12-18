def html_builder():
  from jinja2 import Template
  import webbrowser
  from utils.data_dict import character_json, character_data
  # Load the HTML template
  with open('test_character_data.html', 'r') as file:
      template = Template(file.read())

  data = character_data

  # Render the template with the data
  html_output = template.render(data)

  # Save the generated HTML to a file
  with open('output.html', 'w') as output_file:
      output_file.write(html_output)

  print("HTML file generated successfully.")
  webbrowser.open("output.html")
