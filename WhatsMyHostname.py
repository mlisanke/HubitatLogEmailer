import socket
import platform 

def get_hostname(): 

	name = socket.gethostname()
	node = platform.node()

	return((name,node))

if __name__=="__main__":
	print("My (name,node) is: {}".format(get_hostname()))
