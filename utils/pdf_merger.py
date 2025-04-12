
from PyPDF2 import PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def preencher_template_canva(template_path, dados, output_path):
    """
    Preenche o template do Canva com os dados da proposta
    """
    # Criar PDF temporário com os dados
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    
    # Adicionar dados - ajuste as coordenadas conforme seu template
    c.drawString(100, 750, f"Cliente: {dados['cliente']}")
    c.drawString(100, 730, f"Valor: R$ {dados['valor']:.2f}")
    c.drawString(100, 710, f"Data: {dados['data']}")
    c.drawString(100, 690, f"Descrição: {dados['descricao']}")
    
    c.save()
    packet.seek(0)
    
    # Mesclar com template
    template_pdf = PdfReader(open(template_path, "rb"))
    overlay_pdf = PdfReader(packet)
    
    output = PdfWriter()
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output.add_page(page)
    
    with open(output_path, "wb") as output_file:
        output.write(output_file)
