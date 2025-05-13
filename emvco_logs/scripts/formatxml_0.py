import xml.dom.minidom

def pretty_print_xml(xml_string):
    # Parse the XML
    parsed_xml = xml.dom.minidom.parseString(xml_string)
    
    # Retrieve encoding from the original XML string
    encoding_declaration = '<?xml version="1.0" encoding="utf-8"?>'
    
    # Pretty print the XML with indentation
    formatted_xml = parsed_xml.toprettyxml(indent="  ")
    
    # Check for the XML declaration in the pretty printed XML and remove it if found
    if formatted_xml.startswith('<?xml'):
        formatted_xml = formatted_xml.split('\n', 1)[1]
    
    # Prepend the encoding declaration to the formatted XML
    formatted_xml = encoding_declaration + '\n' + formatted_xml
    
    return formatted_xml

def format_xml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_string = file.read()
        
    formatted_xml = pretty_print_xml(xml_string)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(formatted_xml)

# Use the function with your file path
# file_path = r"C:\Users\f94gdos\Downloads\New folder (8)\L3_2025-05-13-1224\L3_2025-05-13-1224.xml"
# format_xml_file(file_path)
