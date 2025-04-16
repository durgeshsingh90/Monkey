import os
import shutil
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import logging

logger = logging.getLogger('astrex_html_filter')

# Get current script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, 'emvco_template.xml')

# Fields to ignore
IGNORE_LIST = {"HDRLEN", "MHDR", "BM1", "BM2"}

def is_ignored_field(field_id):
    return field_id in IGNORE_LIST or (field_id.startswith("HF") and field_id[2:].isdigit())

def pretty_print_xml(element, indent="  "):
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    return "\n".join([line for line in reparsed.toprettyxml(indent=indent).split('\n') if line.strip()])

def run_html2emvco(html_file_path):
    # Output file path
    base_name = os.path.basename(html_file_path)
    output_file_name = base_name.replace('.html', '_emvco.xml')
    output_file_path = os.path.join(os.path.dirname(html_file_path), output_file_name)

    # Copy template
    shutil.copy(TEMPLATE_PATH, output_file_path)

    # Load template XML
    tree = ET.parse(output_file_path)
    root = tree.getroot()

    # Read connection details
    connection_list = root.find(".//ConnectionList")
    connections = {}
    for conn in connection_list.findall('Connection'):
        friendly = conn.find('Protocol/FriendlyName').text
        symbolic = conn.find('Protocol/SymbolicName').text
        client = conn.find('TCPIPParameters/Client').text == 'true'
        conn_id = conn.get('ID')

        for key in (friendly, symbolic):
            if key not in connections:
                connections[key] = {}
            connections[key][client] = conn_id

    online_message_list = root.find(".//OnlineMessageList")
    current_mti = "0100"

    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    tables = soup.find_all('table', cellspacing='0')

    for table in tables:
        rows = table.find_all('tr')
        online_message = None

        for row in rows:
            headers = row.find_all('th')
            if headers:
                info = headers[0].get_text(strip=True).replace('\xa0', ' ')
                class_type = "REQUEST" if "Received by" in info else "RESPONSE"
                source = destination = None

                for system in connections:
                    if system in info:
                        source = connections[system][True] if class_type == 'REQUEST' else connections[system][False]
                        destination = connections[system][False] if class_type == 'REQUEST' else connections[system][True]
                        break

                if class_type and source and destination:
                    online_message = ET.SubElement(online_message_list, "OnlineMessage", Class=class_type, Source=source, Destination=destination)

            cells = row.find_all('td')
            if cells and online_message:
                field_id = cells[0].get_text(strip=True)

                cell_text = ' | '.join(cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells)
                if "Raw data" in cell_text:
                    raw_data = next((cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells if "bytes:" in cell.get_text(strip=True)), None)
                    if raw_data:
                        ET.SubElement(online_message, "RawData").text = raw_data.split("bytes: ")[1]
                elif "DE007" in field_id:
                    date_cell = next((cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells if "[" in cell.get_text(strip=True)), None)
                    if date_cell:
                        dt = datetime.strptime(date_cell.split("[")[1].split("]")[0], "%Y-%m-%d %H:%M:%S").isoformat() + 'Z'
                        msg_info = ET.SubElement(online_message, "MessageInfo")
                        ET.SubElement(msg_info, "Date-Time").text = dt
                elif "MTI" in field_id:
                    current_mti = cells[6].get_text(strip=True).replace(" ", "")
                    create_field_element(online_message, cells, current_mti)
                else:
                    create_field_element(online_message, cells, current_mti)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(pretty_print_xml(root))
    import zipfile

    # Create ZIP file path
    zip_path = output_file_path.replace('.xml', '.zip')

    # Zip the XML file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(output_file_path, os.path.basename(output_file_path))

    # Optionally delete the original XML after zipping
    os.remove(output_file_path)

    return zip_path  # Return path to the ZIP instead of XML



def create_field_element(online_message, cells, current_mti):
    field_id = cells[0].get_text(strip=True)
    if is_ignored_field(field_id):
        return

    friendly = cells[1].get_text(strip=True)
    field_type = cells[2].get_text(strip=True)
    binary = cells[4].get_text(strip=True)
    viewable = cells[6].get_text(strip=True).replace(" ", "")
    comment = cells[7].get_text(strip=True)

    field_list = online_message.find("FieldList")
    if field_list is None:
        field_list = ET.SubElement(online_message, "FieldList")

    if field_id != "MTI":
        field_id = f"NET.{current_mti}.DE.{field_id[2:]}"

    field = ET.SubElement(field_list, "Field", ID=field_id)
    ET.SubElement(field, "FriendlyName").text = friendly
    ET.SubElement(field, "FieldType").text = field_type
    ET.SubElement(field, "FieldBinary").text = binary
    ET.SubElement(field, "FieldViewable").text = viewable
    if comment:
        ET.SubElement(field, "ToolComment").text = comment
        ET.SubElement(field, "ToolCommentLevel").text = "INFO"
    ET.SubElement(field, "FieldList")
