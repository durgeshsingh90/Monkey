from lxml import etree
import os

def remove_repeated_nodes(element):
    seen_tags = set()
    for parent in element.iter():
        # Create a list of children to avoid modifying the element during iteration
        children_to_remove = []
        for child in parent:
            tag_tuple = (parent.tag, child.tag)
            if tag_tuple in seen_tags:
                children_to_remove.append(child)
            else:
                seen_tags.add(tag_tuple)
        # Remove all children that are marked for removal
        for child in children_to_remove:
            parent.remove(child)
    
    # Handle nested elements to remove repeated tags at all levels
    for child in element:
        remove_repeated_nodes(child)

def main():
    # The specific XML file path
    xml_file = r"C:\Users\f94gdos\Desktop\L3_2025-03-19-1722.xml"
    
    # Parse the XML data into an ElementTree object
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Remove repeated tags
    remove_repeated_nodes(root)

    # Generate the modified file name by appending '_no_repeats' before the file extension
    base, ext = os.path.splitext(xml_file)
    modified_xml_file = f"{base}_no_repeats{ext}"
    
    # Write the modified XML back to the modified file
    tree.write(modified_xml_file, pretty_print=True, encoding='UTF-8', xml_declaration=True)

    # Print the path of the modified file to provide feedback
    print(f"Modified file saved as: {modified_xml_file}")

if __name__ == '__main__':
    main()
