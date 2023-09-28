# %%
# We can't import any self made functions because this uses a different intrepreter

# %%
from fpdf import FPDF

pdf = FPDF()


# %%
def text_to_pdf():
 
    # Stats section
    from fpdf import FPDF

    def PDF_Char_Sheet():
        pdf = FPDF()
        pdf.add_page()
        
        # Draw a title
        pdf.set_font("Arial", size=40)
        pdf.text(15, 15, "Ability Scores:")

        # Add text inside the ellipse
        pdf.set_font("Arial", size=12)
    
        
        # Draw a rectangle
        pdf.set_line_width(1)
        pdf.set_fill_color(0, 255, 0)
        pdf.rect(20, 20, 35, 60)
        
        # Add text inside the rectangle
        pdf.set_text_color(0, 0, 0)  # Text color (black in this example)
        pdf.text(30, 25, "STR")
        pdf.text(45, 25, "10")
        pdf.text(30, 35, "DEX:")
        pdf.text(45, 35, "10")

        pdf.text(30, 45, "CON:")
        pdf.text(45, 45, "10")
        pdf.text(30, 55, "WIS:")
        pdf.text(45, 55, "10")

        pdf.text(30, 65, "INT:")
        pdf.text(45, 65, "10")
        pdf.text(30, 75, "CHA:")
        pdf.text(45, 75, "10")


        pdf.output('PDF_Char_Sheet.pdf')


        #Personality Traits
        #
        #
        #

    if __name__ == '__main__':
        PDF_Char_Sheet()

# %%
text_to_pdf()

# %%




#incorrectly reads the PDF and inputs in a different area (probably just a better idea to create a custom PDF with the data filled in)
import fitz  # PyMuPDF

def insert_text_into_pdf(text_file_path, pdf_template_path, output_pdf_path):
    # Open the existing PDF template
    pdf_document = fitz.open(pdf_template_path)

    # Read the text content from the text file
    with open(text_file_path, 'r', encoding='utf-8') as text_file:
        text_content = text_file.read()

    # Debug: Print the entire text content
    print("Text Content:")
    print(text_content)

    # Split the text content into lines
    text_lines = text_content.split('\n')

    # Iterate over pages and insert the text
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        for line_num, line in enumerate(text_lines):
            # Skip empty or whitespace-only lines
            if line.strip():  # Check if the line has non-whitespace characters
                # Insert each non-empty line of text
                coordinates = (page.rect.width // 4, page.rect.height // 4 + line_num * 12)
                print(f"Inserting at coordinates {coordinates}: {line}")  # Debugging print
                page.insert_text(coordinates, line)  # Adjust the Y position as needed

    # Save the modified PDF to a new file
    pdf_document.save(output_pdf_path)

# Example usage
text_file_path = 'C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_84026730491_character_sheet.txt'  # Replace with the path to your text file
pdf_template_path = 'C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/The_Improved_Pathfinder_Character_Sheet_v1.0.pdf'  # Replace with the path to your PDF template 
output_pdf_path = 'C:/Users/Daniel/Dropbox/My PC (DESKTOP-NEM7B1P)/Desktop/Randomized Character Sheet Generator/_84026730491_character_sheet.pdf'  # Replace with the desired output PDF path



insert_text_into_pdf(text_file_path, pdf_template_path, output_pdf_path)

# %%
