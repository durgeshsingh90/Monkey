import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import shutil
import os
from datetime import datetime
import xml.dom.minidom

# Function to generate search symbol based on friendly name
def generate_search_symbol(friendly_name):
    words = friendly_name.split()
    if len(words) > 2:
        # More than 2 words - take the 1st letter of each word and combine in caps
        search_symbol = ''.join(word[0] for word in words).upper()
    elif len(words) == 2:
        # Two words - merge the two words and make it uppercase
        search_symbol = (words[0] + words[1]).upper()
    else:
        # One word - make it uppercase
        search_symbol = friendly_name.upper()
    return search_symbol

# Define paths
html_file_path = r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__filtered_20250327_202308\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__filtered_20250327_202308.html"
template_path = r"C:\Durgesh\Office\Automation\Monkey\Monkey\python\astrex_html_logfilter\emvco_template.xml"

# Prepare the output path (remove timestamp, keeping '_emvco' suffix)
base_name = os.path.basename(html_file_path)
output_file_name = base_name.replace('.html', '_emvco.xml')
output_file_path = os.path.join(os.path.dirname(html_file_path), output_file_name)

# Create a copy of the template
shutil.copy(template_path, output_file_path)

# Parse the copied XML file
tree = ET.parse(output_file_path)
root = tree.getroot()

# Read connection details from XML
connection_list = root.find(".//ConnectionList")
connections = {}
for connection in connection_list.findall('Connection'):
    friendly_name = connection.find('Protocol/FriendlyName').text
    symbolic_name = connection.find('Protocol/SymbolicName').text
    client = connection.find('TCPIPParameters/Client').text == 'true'
    conn_id = connection.get('ID')
    
    if friendly_name not in connections:
        connections[friendly_name] = {}
    if symbolic_name not in connections:
        connections[symbolic_name] = {}
    
    connections[friendly_name][client] = conn_id
    connections[symbolic_name][client] = conn_id

# Find the OnlineMessageList element
online_message_list = root.find(".//OnlineMessageList")

# Define the list of field IDs to ignore
ignore_list = {"HDRLEN", "MHDR", "BM1", "BM2"}

# Define the list of field IDs for which to add search symbols
search_symbol_field_ids = {"DE002", "DE003", "DE004"}  # example field IDs

# To store the current MTI value
current_mti = "0100"

# Read the HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extract table data and create OnlineMessage elements
tables = soup.find_all('table', cellspacing='0')

# Function to determine class, source, and destination
def determine_class_source_destination(message, connections):
    class_type = "REQUEST" if "Received by" in message else "RESPONSE"
    
    for system in connections:
        if system in message:
            source = connections[system][True] if class_type == 'REQUEST' else connections[system][False]
            destination = connections[system][False] if class_type == 'REQUEST' else connections[system][True]
            return class_type, source, destination
    
    return None, None, None

def is_ignored_field(field_id):
    if field_id in ignore_list:
        return True
    if field_id.startswith("HF") and field_id[2:].isdigit():
        return True
    return False

def process_field_type(field_type, field_id):
    if field_id.startswith("DE.") and field_type[1:].isdigit():
        number_part = int(field_type[1:]) * 2
        return f"{field_type[0]}{number_part}"
    return field_type

def create_field_element(parent, id_prefix, cells, subfields=None):
    field_id = cells[0].get_text(strip=True)
    
    if is_ignored_field(field_id):
        return

    friendly_name = cells[1].get_text(strip=True).replace("&", " ")
    field_type = process_field_type(cells[2].get_text(strip=True), field_id)
    field_binary = cells[4].get_text(strip=True)
    field_viewable = cells[6].get_text(strip=True).replace(" ", "")
    tool_comment = cells[7].get_text(strip=True)
    
    field_list = parent.find("FieldList")
    if field_list is None:
        field_list = ET.SubElement(parent, "FieldList")
    
    if subfields:
        field_id = f"{id_prefix}.{field_id}"
    elif field_id != "MTI":
        field_id = f"{id_prefix}.DE.{field_id[2:]}"
    
    field = ET.SubElement(field_list, "Field", ID=field_id)
    ET.SubElement(field, "FriendlyName").text = friendly_name
    ET.SubElement(field, "FieldType").text = field_type
    ET.SubElement(field, "FieldBinary").text = field_binary
    ET.SubElement(field, "FieldViewable").text = field_viewable
    
    # Add SearchSymbol element for specific fields
    if field_id in search_symbol_field_ids:
        search_symbol_name = generate_search_symbol(friendly_name)
        search_symbol_value = field_viewable
        ET.SubElement(field, "SearchSymbol", Name=search_symbol_name, Value=search_symbol_value)
    
    if tool_comment:
        ET.SubElement(field, "ToolComment").text = tool_comment
        ET.SubElement(field, "ToolCommentLevel").text = "INFO"
    
    return field

# Process each table
for table in tables:
    rows = table.find_all('tr')
    online_message = None  # Reset for each table
    current_field = None

    for row in rows:
        headers = row.find_all('th')
        if headers:
            message_info = headers[0].get_text(strip=True).replace('\xa0', ' ')
            class_type, source, destination = determine_class_source_destination(message_info, connections)
            
            if class_type and source and destination:
                # Create an OnlineMessage element
                online_message = ET.SubElement(online_message_list, "OnlineMessage")
                online_message.set("Class", class_type)
                online_message.set("Source", source)
                online_message.set("Destination", destination)

        cells = row.find_all('td')
        if cells and online_message is not None:
            field_id = cells[0].get_text(strip=True)
            cell_text = ' | '.join(cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells)
            if "Raw data" in cell_text:
                # Extract RawData from the matching cell
                raw_data = next((cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells if "bytes:" in cell.get_text(strip=True)), None)
                if raw_data:
                    raw_data = raw_data.split("bytes: ")[1]  # Get the data after "bytes: "
                    ET.SubElement(online_message, "RawData").text = raw_data
            elif "DE007" in field_id:
                tool_comment = cells[7].get_text(strip=True)
                date_time_text = next((cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells if "[" in cell.get_text(strip=True)), None)
                if date_time_text:
                    date_time = date_time_text.split("[")[1].split("]")[0]
                    date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").isoformat() + 'Z'
                    # Create MessageInfo element after RawData
                    message_info_element = ET.Element("MessageInfo")
                    ET.SubElement(message_info_element, "Date-Time").text = date_time
                    # Find the index of RawData to insert after it
                    raw_data_index = list(online_message).index(online_message.find("RawData")) + 1
                    online_message.insert(raw_data_index, message_info_element)
                current_field = create_field_element(online_message, f"NET.{current_mti}", cells)
            elif "MTI" in field_id:
                current_mti = cells[6].get_text(strip=True).replace(" ", "")
                current_field = create_field_element(online_message, f"NET.{current_mti}", cells)
            elif field_id.startswith("DE") and not field_id[3:].isdigit():
                if current_field:
                    create_field_element(current_field, f"NET.{current_mti}.DE.{field_id[2:5]}", cells, subfields=True)
            else:
                # Create FieldList entry for other fields
                current_field = create_field_element(online_message, f"NET.{current_mti}", cells)

# Function to pretty-print and format XML with indents and new lines
def pretty_print_xml(element, indent="  "):
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_xml_str = reparsed.toprettyxml(indent=indent)
    # Strip unnecessary blank lines
    return "\n".join([line for line in pretty_xml_str.split('\n') if line.strip()])

# Save the modified XML to the output file with pretty printing
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.write(pretty_print_xml(root))

print(f"XML log has been updated and saved to {output_file_path}")
