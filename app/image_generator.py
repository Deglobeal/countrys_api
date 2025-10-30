import os
from datetime import datetime
from typing import List
from schemas import CountryResponse

def generate_summary_image(countries: List[CountryResponse], total_countries: int, refresh_timestamp: datetime):
    """Generate summary image using reportlab"""
    
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import tempfile
        
        # Create a PDF first, then convert to PNG
        pdf_path = 'cache/summary.pdf'
        png_path = 'cache/summary.png'
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, height - 100, "Country Data Summary")
        
        # Total countries
        c.setFont("Helvetica", 14)
        c.drawString(100, height - 140, f"Total Countries: {total_countries}")
        
        # Top 5 countries by GDP
        c.drawString(100, height - 180, "Top 5 Countries by Estimated GDP:")
        
        # Filter countries with GDP data and sort
        countries_with_gdp = [c for c in countries if c.estimated_gdp is not None]
        top_countries = sorted(countries_with_gdp, key=lambda x: x.estimated_gdp, reverse=True)[:5] # type: ignore
        
        y_position = height - 220
        for i, country in enumerate(top_countries, 1):
            gdp_str = f"${country.estimated_gdp:,.2f}" if country.estimated_gdp else "N/A"
            text = f"{i}. {country.name}: {gdp_str}"
            c.drawString(120, y_position, text)
            y_position -= 30
        
        # Timestamp
        timestamp_str = refresh_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        c.drawString(100, y_position - 40, f"Last Refreshed: {timestamp_str}")
        
        c.save()
        
        # Convert PDF to PNG (simple approach - we'll use the PDF as is for now)
        # For a real PNG, we'd need additional libraries, but let's create a simple workaround
        
        # Create a simple PNG using reportlab's drawing capabilities
        create_simple_png(countries, total_countries, refresh_timestamp, png_path)
        
        return png_path
        
    except Exception as e:
        print(f"Image generation failed: {e}")
        # Create a simple text-based PNG as fallback
        create_fallback_image(total_countries, refresh_timestamp)
        return 'cache/summary.png'

def create_simple_png(countries, total_countries, refresh_timestamp, png_path):
    """Create a simple PNG using reportlab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from reportlab.graphics import renderPM
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        
        # Create a drawing
        d = Drawing(400, 300)
        
        # Add title
        title = String(150, 280, "Country Data Summary")
        title.fontName = 'Helvetica-Bold'
        title.fontSize = 16
        d.add(title)
        
        # Add total countries
        total_text = String(50, 250, f"Total Countries: {total_countries}")
        total_text.fontName = 'Helvetica'
        total_text.fontSize = 12
        d.add(total_text)
        
        # Add timestamp
        timestamp_str = refresh_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        time_text = String(50, 230, f"Last Updated: {timestamp_str}")
        time_text.fontName = 'Helvetica'
        time_text.fontSize = 10
        d.add(time_text)
        
        # Save as PNG
        renderPM.drawToFile(d, png_path, fmt='PNG')
        
    except Exception as e:
        print(f"Simple PNG creation failed: {e}")
        create_fallback_image(total_countries, refresh_timestamp)

def create_fallback_image(total_countries, refresh_timestamp):
    """Create a basic fallback image"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.graphics import renderPM
        from reportlab.graphics.shapes import Drawing, String
        
        d = Drawing(400, 200)
        
        title = String(100, 150, "Country Data Summary")
        title.fontName = 'Helvetica-Bold'
        title.fontSize = 16
        d.add(title)
        
        total_text = String(100, 120, f"Total Countries: {total_countries}")
        total_text.fontName = 'Helvetica'
        total_text.fontSize = 12
        d.add(total_text)
        
        timestamp_str = refresh_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        time_text = String(100, 100, f"Last Updated: {timestamp_str}")
        time_text.fontName = 'Helvetica'
        time_text.fontSize = 10
        d.add(time_text)
        
        renderPM.drawToFile(d, 'cache/summary.png', fmt='PNG')
        
    except Exception as e:
        print(f"Fallback image creation failed: {e}")
        # Create absolute minimum - a 1x1 pixel PNG
        with open('cache/summary.png', 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x00\x00\x00\x00IEND\xaeB`\x82')