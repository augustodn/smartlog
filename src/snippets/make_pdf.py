import jinja2
import pdfkit
import os

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "template.html"
template = templateEnv.get_template(TEMPLATE_FILE)

well = {
    'name': 'TPT.Nq.CLN.x-2',
    'field': 'LOS TOLDOS',
    'area': '',
    'province': 'NEUQUEN',
    'country': 'ARGENTINA',
    'company': 'TECPETROL',
    'driller': '',
    'operator': 'Cristian Albaine',
    'witness': '',
    'date': '05-Abril-2019',
    'service': 'CEMENTACION RADIAL\n RAYOS GAMMA',
    'casing': '7',
    'comments': 'Registro sin novedades',
    'footNote': """Este registro a escala se ofrece como control """
                """de la operacion. Se entrega solo un original.""",
    'inDate': ''
}

outputText = template.render(well = well)
html_file = open("temp.html", 'w')
html_file.write(outputText)
html_file.close()
pdfkit.from_file('temp.html', 'template.pdf')
os.remove('temp.html')
