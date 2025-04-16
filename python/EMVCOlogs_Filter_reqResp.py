import os
import xml.etree.ElementTree as ET

# Summary of Changes
# Adjust the keep logic: Added a flag keep to signal when a matching request message has been found.
# Retain the following message: When a matching message is found, the flag keep ensures that the immediate subsequent message is also retained.
# Reset the keep flag after the subsequent message is processed.

def element_to_string(element):
    """Convert element text and all subelement text to a single string."""
    content = []
    for elem in element.iter():
        if elem.text:
            content.append(elem.text.strip())
    return " ".join(content)

def evaluate_conditions(content, conditions):
    """Evaluate complex conditions within the given content."""
    def parse_condition(condition):
        if ' AND ' in condition:
            sub_conditions = condition.split(' AND ')
            return all(parse_condition(sub) for sub in sub_conditions)
        elif ' OR ' in condition:
            sub_conditions = condition.split(' OR ')
            return any(parse_condition(sub) for sub in sub_conditions)
        elif ' NOT ' in condition:
            sub_conditions = condition.split(' NOT ')
            return not parse_condition(sub_conditions[1])
        else:
            return condition in content

    return parse_condition(conditions)

def filter_online_messages(xml_file, conditions):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    online_message_list = root.find('OnlineMessageList')
    if online_message_list is not None:
        to_remove = []
        keep = False

        # Iterate over online messages
        for online_message in online_message_list.findall('OnlineMessage'):
            content = element_to_string(online_message)  # Convert element to string for searching
            if evaluate_conditions(content, conditions):
                keep = True  # Mark to keep the message and the next one
            elif keep:
                keep = False  # Reset keep flag after keeping one additional message
            else:
                to_remove.append(online_message)  # Mark message for removal

        # Remove messages that didn't meet the conditions
        for online_message in to_remove:
            online_message_list.remove(online_message)

    # Construct the output filename
    base_name, ext = os.path.splitext(xml_file)
    output_file = f"{base_name}_pspfiltered{ext}"

    # Write the modified XML back to a file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

    print(f"Filtered XML has been saved to: {output_file}")

if __name__ == "__main__":
    xml_file = r"C:\Users\f94gdos\Desktop\TP\L3_2025-03-19-1722.xml"
    conditions = '456896'  # Search condition string with AND, OR, NOT

    filter_online_messages(xml_file, conditions)
