from binascii import hexlify
import os, socket, sys, threading, traceback, SocketServer, logging, paramiko, time
from paramiko.py3compat import b, u

try:
	import console
	console.set_color(1,1,0)
	console.set_font("Menlo",10)
	print """
	   __ __                             __ 
	  / // /__  ___  ___ __ _____  ___  / /_
	 / _  / _ \/ _ \/ -_) // / _ \/ _ \/ __/
	/_//_/\___/_//_/\__/\_, / .__/\___/\__/ 
	                   /___/_/ """
	console.set_color()
	console.set_font()
except:
	print """
	   __ __                             __ 
	  / // /__  ___  ___ __ _____  ___  / /_
	 / _  / _ \/ _ \/ -_) // / _ \/ _ \/ __/
	/_//_/\___/_//_/\__/\_, / .__/\___/\__/ 
	                   /___/_/ """       

PORT = 2222
LOG_FILE = "Honeypot.log"
msg1 = "\t[1;43;37m   -=-=- Honeypot v1.3.3 -=-=-   \r\n"
DENY_ALL = False
PASSWORDS = [
"root",
"password",
"test"
]

def deepscan(target,f=None):
	data = str(socket.gethostbyaddr(target))
	data = data.replace(",","").replace("[","").replace("]","").replace("(","").replace(")","").replace("'","")
	data = data.split()
	d1 = "-Name: "+data[0]
	d2 = "-FQDN: "+data[1]
	d3 = "-Provider: "+data[2]
	print d1
	print d2
	print d3
	f.write("-"+target+"\n")
	f.write(d1+"\n")
	f.write(d2+"\n")
	f.write(d3+"\n\n")
	print ""

def deepscan2(target,chan):
	data = str(socket.gethostbyaddr(target))
	data = data.replace(",","").replace("[","").replace("]","").replace("(","").replace(")","").replace("'","")
	data = data.split()
	d1 = "-Name: "+data[0]
	d2 = "-FQDN: "+data[1]
	d3 = "-Provider: "+data[2]
	chan.send("\t"+d1+"\r\n")
	chan.send("\t"+d2+"\r\n")
	chan.send("\t"+d3+"\r\n")

logger = logging.getLogger("access.log")
logger.setLevel(logging.INFO)
lh = logging.FileHandler(LOG_FILE)
logger.addHandler(lh)

host_key = paramiko.RSAKey(filename="rsa.key")

print "\nKey: " + u(hexlify(host_key.get_fingerprint()))
print ""

class Server(paramiko.ServerInterface):
	def __init__(self, client_address):
		self.event = threading.Event()
		self.client_address = client_address
	
	def check_channel_request(self, kind, chanid):
		if kind == "session":
			return paramiko.OPEN_SUCCEEDED
		return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
	
	def check_auth_password(self, username, password):
		logger.info("-=-=- %s -=-=-\nUser: %s\nPassword: %s\n" % (self.client_address[0], username, password))
		
		print " IP: %s\n User: %s\n Pass: %s" % (self.client_address[0], username, password)
			
		if DENY_ALL == True:
			return paramiko.AUTH_FAILED
		f = open("blocked.dat","r")
		data = str(f.readlines()).find(self.client_address[0])
		if data > 1:
			return paramiko.BadAuthenticationType
		else:
			f = open("blocked.dat","a")
			deepscan(self.client_address[0],f)
		paramiko.OPEN_FAILED_CONNECT_FAILED
		if (username == "root") and (password in PASSWORDS):
			return paramiko.AUTH_SUCCESSFUL
		return paramiko.AUTH_FAILED
	
	def check_channel_shell_request(self, channel):
		self.event.set()
		return True
	
	def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
		return True

class SSHHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		try:
			t = paramiko.Transport(self.connection)
			t.add_server_key(host_key)
			server = Server(self.client_address)
			try:
				t.start_server(server=server)
			except paramiko.SSHException:
				print "*** SSH Failed"
				return
			
			chan = t.accept(20)
			if chan is None:
				t.close()
				return
			
			server.event.wait(10)
			if not server.event.is_set():
				t.close()
				return
			
			chan.send(msg1 + "\t")
			for i in range(101):
				chan.send("\r\t\t Loading "+str(i)+" of 100 ")
				time.sleep(0.001)
			chan.send("\r\n\r\n\tCongrats All Cerious Hackers!\r\n\tYou have all walked into a Honeypot!\r\n\tYou will now be blocked from joining \r\n\tthis server and your IP address\r\n\tinformation has been reported into the\r\n\tfollowing report:\r\n\r\n")
			deepscan2(self.client_address[0],chan)
			
			chan.send("\r\n\r\n\r\n\tNow GTFO my Honeypot")
			chan.close()
			
		except Exception as e:
			print("*** Caught exception: " + str(e.__class__) + ': ' + str(e))
			traceback.print_exc()
		finally:
			try:
				t.close()
			except:
				pass

sshserver = SocketServer.ThreadingTCPServer(("192.168.1.76", PORT), SSHHandler)
sshserver.serve_forever()
