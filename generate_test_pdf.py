from fpdf import FPDF

# Create a PDF object
pdf = FPDF()
pdf.add_page()

# Set font: Arial, Bold, size 16 for the title
pdf.set_font("Arial", 'B', 16)
pdf.cell(0, 10, "Fake Pitch Deck", ln=True, align="C")

# Add a line break
pdf.ln(10)

# Set font: Arial, size 12 for the content
pdf.set_font("Arial", size=12)

# Fake content for the pitch deck
content = (
    "Executive Summary:\n"
    "Our company is revolutionizing the tech industry with an innovative product that streamlines processes and boosts productivity.\n\n"
    "Market Opportunity:\n"
    "The market for our product is vast, with millions of potential customers worldwide and growing demand for digital transformation solutions.\n\n"
    "Competitive Landscape:\n"
    "We face competition from established firms, but our unique approach and advanced technology give us a significant edge.\n\n"
    "Financial Highlights:\n"
    "With strong revenue growth projections, low operating costs, and a robust business model, we are poised for rapid expansion.\n"
)

# Add the content as multiple cells (multi_cell will wrap text)
pdf.multi_cell(0, 10, content)

# Save the PDF to a file
pdf.output("test_pitch_deck.pdf")
