###############################################################################
#
# Filename: mds_db.py
# Author: Jose R. Ortiz and ... (hopefully some students contribution)
#
# Description:
# 	Copy client for the DFS
#
#

import socket
import sys
import os.path

from Packet import *

def usage():
	print """Usage:\n\tFrom DFS: python %s <server>:<port>:<dfs file path> <destination file>\n\tTo   DFS: python %s <source file> <server>:<port>:<dfs file path>""" % (sys.argv[0], sys.argv[0])
	sys.exit(0)

def communications(command, IP, Port):
	#creating socket
	s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)

	#connecting to metadata server
	try:
	    s.connect ((IP, int(Port)))
	except socket.error, e:
	    print "Could not connect with server.\n %s"%e
	    sys.exit(1)

	print "Connected to IP:%s on PORT:%s."%(IP, Port)   

	s.sendall(command)
	response = s.recv(1024)


	return response, s

def copyToDFS(address, fname, path):
	""" Contact the metadata server to ask to copu file fname,
	    get a list of data nodes. Open the file in path to read,
	    divide in blocks and send to the data nodes. 
	"""

	# Create a connection to the data server

	# Fill code
	# Create a socket (SOCK_STREAM means a TCP socket)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
	    sock.connect((address[0], address[1]))
	except socket.error, e:
	    print "Could not connect with server.\n %s"%e
	    sys.exit(1)
	print "Connected to metadata server."

	# Read File.
	f = open(path, 'r')
	contents = f.read()
	fsize = len(contents)

	# Create a Put packet with the fname and the length of the data,
	# and sends it to the metadata server 
	try:
		response = "DUP"
		sp = Packet()
		while response == "DUP":
			sp.BuildPutPacket(fname, fsize)
			sock.sendall(sp.getEncodedPacket())
			response = sock.recv(1024)

			if response != "DUP":
			 	sp.DecodePacket(response)
			 	dnservers = sp.getDataNodes()
			if response == "DUP":
				print "File exists or error."
				sys.exit(1)
	finally:
		sock.close()

	# If no error or file exists
	# Get the list of data nodes.
	# Divide the file in blocks
	# Send the blocks to the data servers

	# Fill code	
	blocksize = fsize/len(dnservers)
	extra = fsize%len(dnservers)
	blocks = []
	f.seek(0)

	for i, nodes in enumerate(dnservers):
		blockContents = f.read(blocksize)
		if i == len(dnservers)-1:
			blockContents+=f.read(extra)
			blocksize+=extra
		sp.BuildPutPacket(fname, blocksize)
		request, s = communications(sp.getEncodedPacket(), nodes[0], nodes[1])

		if request:
			s.sendall(blockContents)

		else:
			print"Swiggitty swag, node is down! SHEEET!"

		blocks.append((nodes[0], str(nodes[1]), request))
		s.close()


	# Notify the metadata server where the blocks are saved.
	print blocks

	sp.BuildDataBlockPacket(fname, blocks)

	success, s = communications(sp.getEncodedPacket(), address[0], address[1])
	s.close()

	if int(success):
		pass
	else:
		print "An error ocurred while adding the blocks."
		sys.exit(1)

	f.close()

	
def copyFromDFS(address, fname, path):
	""" Contact the metadata server to ask for the file blocks of
	    the file fname.  Get the data blocks from the data nodes.
	    Saves the data in path.
	"""

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
	    sock.connect((address[0], address[1]))
	except socket.error, e:
	    print "Could not connect with server.\n %s"%e
	    sys.exit(1)
	print "Connected to metadata server."

   	# Contact the metadata server to ask for information of fname
   	try:
		sp = Packet()
		sp.BuildGetPacket(fname)
		sock.sendall(sp.getEncodedPacket())
		response = sock.recv(1024)

	 	sp.DecodePacket(response)

	 	nodes = sp.getDataNodes()
		if response == "NFOUND":
			print "File not found."
			sys.exit(1)
	finally:
		sock.close()

	# If there is no error response Retreive the data blocks

	f = open(path, 'w')

	for i in nodes:
		nodeHost, nodePort, blockID = i[0], i[1], i[2]
		sp.BuildGetDataBlockPacket(blockID)
		response, s = communications(sp.getEncodedPacket(), nodeHost, nodePort)
		blocksize, blockContents = response.split('|', 1)
		while len(blockContents) < int(blocksize):
			blockContents += s.recv(1024)
		
		f.write(blockContents)

	f.close()
	s.close()


if __name__ == "__main__":
#	client("localhost", 8000)
	if len(sys.argv) < 3:
		usage()

	file_from = sys.argv[1].split(":")
	file_to = sys.argv[2].split(":")

	if len(file_from) > 1:
		ip = file_from[0]
		port = int(file_from[1])
		from_path = file_from[2]
		to_path = sys.argv[2]

		if os.path.isdir(to_path):
			print "Error: path %s is a directory.  Please name the file." % to_path
			usage()

		copyFromDFS((ip, port), from_path, to_path)

	elif len(file_to) > 2:
		ip = file_to[0]
		port = int(file_to[1])
		to_path = file_to[2]
		from_path = sys.argv[1]

		if os.path.isdir(from_path):
			print "Error: path %s is a directory.  Please name the file." % from_path
			usage()

		copyToDFS((ip, port), to_path, from_path)


