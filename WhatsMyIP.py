from urllib.request import urlopen 

def get_external_ip(): 
	try:
        # checkip.amazonaws.com simply responds with your public IP as 
        # plain text
        	with urlopen("https://checkip.amazonaws.com", timeout=5) as response:
            		return response.read().decode("utf-8").strip() 
	except Exception as e:
        	return f"Error fetching IP: {e}"

if __name__=="__main__":
	print(f"My External Public IP: {get_external_ip()}")
