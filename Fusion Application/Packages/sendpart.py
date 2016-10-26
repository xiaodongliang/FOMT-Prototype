from . import requests


def send(url, payload_data, step_file, time, verification=True):
    # Set default message
    message = "Unfortunately, there are invalid entries in your project form. Please check the entries in your project form and try submitting again."

    # Send to platform
    try:
        # Get response
        res = requests.post(url, data=payload_data, files=step_file, timeout=time, verify=verification)

        # Check status
        if res.status_code == 200:  # success
            message = "Thank you for submitting your project to Xiaodong Test, "
           

        else:  # failure/res.status_code==422           
            message = str(res.status_code)

    # Connection timed out
    except requests.exceptions.ConnectTimeout:
        message = "Connection timed out."

    # Failed to connect
    except requests.exceptions.ConnectionError:
        message = "Connection erroraa."
    
        
    # Return result
    return message
