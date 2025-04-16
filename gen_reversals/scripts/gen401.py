import datetime
import json

# def get_user_input():
#     print("Please enter the 0100 authorization request message in JSON format (press Enter twice to complete):")
#     input_message = ""
#     while True:
#         line = input()
#         if line == "":
#             break
#         input_message += line + "\n"
#     auth_request = json.loads(input_message)

#     print("Please enter the 0110 authorization response message in JSON format (press Enter twice to complete):")
#     input_message = ""
#     while True:
#         line = input()
#         if line == "":
#             break
#         input_message += line + "\n"
#     auth_response = json.loads(input_message)

#     return auth_request, auth_response

def create_reversal_0401_message(auth_request, auth_response):
    reversal_message = {}

    # Copying mandatory data elements from the auth request
    reversal_message['mti'] = 401
    reversal_message['data_elements'] = {}
    
    de_req = auth_request['data_elements']
    de_res = auth_response['data_elements']

    reversal_message['data_elements']['DE002'] = de_req['DE002']
    reversal_message['data_elements']['DE003'] = de_req['DE003']
    reversal_message['data_elements']['DE004'] = de_req['DE004']
    
    # System Time in GMT
    reversal_message['data_elements']['DE007'] = datetime.datetime.utcnow().strftime('%m%d%H%M%S')
    
    reversal_message['data_elements']['DE011'] = de_req['DE011']
    reversal_message['data_elements']['DE012'] = de_req['DE012']
    reversal_message['data_elements']['DE013'] = de_req['DE013']
    if 'DE014' in de_req:
        reversal_message['data_elements']['DE014'] = de_req['DE014']
    if 'DE015' in de_res:
        reversal_message['data_elements']['DE015'] = de_res['DE015']
    reversal_message['data_elements']['DE018'] = de_req['DE018']
    reversal_message['data_elements']['DE019'] = de_req['DE019']
    reversal_message['data_elements']['DE022'] = de_req['DE022']
    if 'DE023' in de_req:
        reversal_message['data_elements']['DE023'] = de_req['DE023']
    reversal_message['data_elements']['DE025'] = de_req['DE025']
    reversal_message['data_elements']['DE032'] = de_req['DE032']
    reversal_message['data_elements']['DE037'] = de_req['DE037']
    if 'DE038' in de_res:
        reversal_message['data_elements']['DE038'] = de_res['DE038']
    if 'DE039' in de_res:
        reversal_message['data_elements']['DE039'] = de_res['DE039']
    reversal_message['data_elements']['DE041'] = de_req['DE041']
    reversal_message['data_elements']['DE042'] = de_req['DE042']
    reversal_message['data_elements']['DE043'] = de_req['DE043']
    if 'DE044' in de_res:
        reversal_message['data_elements']['DE044'] = de_res['DE044']
    reversal_message['data_elements']['DE049'] = de_req['DE049']
    
    optional_fields = ['DE054', 'DE055', 'DE060', 'DE061', 'DE062', 'DE064', 'DE065', 'DE066', 'DE095', 'DE128']
    
    for field in optional_fields:
        if field in de_req:
            reversal_message['data_elements'][field] = de_req[field]
    
    # Reversal Reason Code
    reversal_message['data_elements']['DE063'] = "109"  # Reversal reason code
    
    # If DE062 is present in the 0110 response, extract BM62.2 and BM62.23
    if 'DE062' in de_res:
        de062 = de_res['DE062']
        reversal_message['data_elements']['DE062'] = {}
        if '02' in de062:
            reversal_message['data_elements']['DE062']['02'] = de062['02']
        if '23' in de062:
            reversal_message['data_elements']['DE062']['23'] = de062['23']
    
    # Create DE090 in the specified format
    reversal_message['data_elements']['DE090'] = format_original_data_elements(auth_request)
    
    return reversal_message

def format_original_data_elements(auth_request):
    de = auth_request['data_elements']
    original_data_elements = (
        f"{auth_request['mti']:04}" +
        f"{de['DE011']:06}" +
        f"{de['DE007']:010}" +
        f"{de.get('DE032', '').zfill(11):>11}"[:11] +  # Acquiring institution identification code (11 digits)
        f"{de.get('DE032', '').zfill(11):>11}"[:11]  # Forwarding institution identification code (11 digits)
    )

    return {
        "orig_mti": original_data_elements[:4],
        "orig_stan": original_data_elements[4:10],
        "orig_xmsn_datetime": original_data_elements[10:20],
        "orig_acq_id": original_data_elements[20:31],
        "orig_frwd_id": original_data_elements[31:42]
    }

# def main():
#     auth_request, auth_response = get_user_input()
#     reversal_message = create_reversal_0401_message(auth_request, auth_response)
#     print(json.dumps(reversal_message, indent=4))

# if __name__ == "__main__":
#     main()
