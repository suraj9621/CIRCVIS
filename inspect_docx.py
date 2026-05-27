from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

p = Path(r'C:/Users/ANURAG-G/Desktop/CIRCVIS (2)/CIRCVIS/Meher_Jeevan__M(8)_Practical_Image Processing and Panorama Creation using Python, OpenCV and NumPy.docx')
if not p.exists():
    raise FileNotFoundError(p)
with ZipFile(p) as z:
    xml = z.read('word/document.xml')
root = ET.fromstring(xml)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
paragraphs = []
for par in root.findall('.//w:p', ns):
    texts = [t.text for t in par.findall('.//w:t', ns) if t.text]
    if texts:
        paragraphs.append(''.join(texts))
for i, para in enumerate(paragraphs[:120], start=1):
    print(f'{i:03}: {para}')
