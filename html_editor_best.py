def html_builder():
  import jinja2
  import webbrowser
  import json
  from utils.data_dict import character_json

  print("this is it")
  print(character_json)
  character_data = character_json

  # Create a Jinja2 environment
  template_env = jinja2.Environment()

##### Currently the data will overwrite any data in the test_character_sheet, so I've savd the data on character_sheet_true


  # Load the HTML template
  template = template_env.from_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Character Sheet</title>
    </head>
    <body>
      <div class="container">
        <h1>Character Sheet</h1>
      </div>

      <table>
        <tr>
          <th>Attribute</th>
          <th>Value</th>
        </tr>
        {% for key, value in character_data.items() %}
        <tr>
          <td>{{ key }}</td>
          <td>{{ value }}</td>
        </tr>
        {% endfor %}
      </table>
    </body>
    </html>
  """)

  # Render the template with the character data
  rendered_html = template.render(character_data=character_data)

  # Write the rendered HTML to a file
  with open("test_character_data.html", "w") as f:
    f.write(rendered_html)

  # Open the HTML file in the web browser
  webbrowser.open('test_character_data.html')
