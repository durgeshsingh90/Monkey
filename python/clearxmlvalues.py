from lxml import etree
import os

def clear_leaf_nodes(element):
    # Loop through each element in the tree
    for sub_element in element.iter():
        # Check if the current element has any children
        if len(sub_element):
            continue
        # If the element has no children, clear its text but ensure the tag is not deleted
        else:
            sub_element.text = ""

def main():
    # The specific XML file path
    xml_file = r"C:\Users\f94gdos\Desktop\L3_2025-03-19-1722.xml"
    
    # Parse the XML data into an ElementTree object
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Clear the values of tags that do not have further subtags
    clear_leaf_nodes(root)

    # Generate the modified file name by appending '_modified' before the file extension
    base, ext = os.path.splitext(xml_file)
    modified_xml_file = f"{base}_modified{ext}"
    
    # Write the modified XML back to the modified file
    tree.write(modified_xml_file, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    # Print the path of the modified file to provide feedback
    print(f"Modified file saved as: {modified_xml_file}")

if __name__ == '__main__':
    main()
