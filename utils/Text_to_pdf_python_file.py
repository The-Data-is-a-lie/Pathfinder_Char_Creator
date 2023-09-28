# %%



# %%
from fpdf import FPDF

pdf = FPDF()


# %%
def text_to_pdf():
    # Stats section
    from fpdf import FPDF

    def draw_shapes():
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
        pdf.text(30, 25, "STR:")
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


        pdf.output('draw_shapes.pdf')

    if __name__ == '__main__':
        draw_shapes()

# %%
text_to_pdf()

# %%



