import socket,time
import pynmea2

DEFAULT_HOST="localhost"
DEFAULT_PORT=10113
DEFAULT_INTERVAL=2.0


class Sounder:
    IP="10.10.100.254"
    PORT=8899
    INIT_MSG="0x68 0x01 0x06 0x02 0x00 0x00 0x00 0x00 0x00 0x09 0xed"
    REQ_MSG="0x68 0x02 0x01 0x01 0x04 0xED"
    
    def __init__(self):
        self.init()
        
    def init(self):
        try:
            self.sock=socket.socket()
            self.sock.settimeout(5)
            self.sock.connect((self.IP,self.PORT))
            self.sock.send(strFromHex(self.INIT_MSG))
            self.sock.recv(100)
        except socket.timeout:
            print ("Cannot initialize. Check connection to sounder.")
            self.sock=None
        
    def get_value(self):
        self.sock.send(strFromHex(self.REQ_MSG)) #request data
        stream=self.sock.recv(1000)
        #print repr(stream)
        while len(stream)>2 and stream[:2]!='h\x82':
            stream=stream[1:]
        if len(stream)>3: # we got a packet
            if stream[2]=="\x01":
                return "inactive",2000.,2000.,-1.0
            vals=map(ord,stream[3:6]+stream[9])
            #print vals
            #print repr(stream)

            return "active",(16*vals[0]+vals[1]/16)/10., (256*(vals[1]%16)+vals[2])/10.,vals[3]/4.
        else:
            print (stream)    

    def get_nmea(self):
        try:
            a,depth,temp,batt=self.get_value()
        except:
            print ("problem getting value!")
        else:
            msg=pynmea2.DBT("SD","DBT",('',"f",str(depth),"M","","F"))
            return str(msg)+"\r\n"

def strFromHex(l):
    return "".join(map(lambda x: eval("'\\"+x[1:]+"'"),l.split()))


if __name__=="__main__":
    import argparse	
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="the port number to send messages to")
    parser.add_argument("-H", "--host", type=str, help="the host interface")
    
    parser.add_argument("-i", "--interval", type=int, help="interval (in secs) between readings", default=DEFAULT_INTERVAL)    

    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    args = parser.parse_args()

    if not args.host: # Symbolic name meaning the local host
        args.host=DEFAULT_HOST
    if not args.port:
        args.port = DEFAULT_PORT           # Arbitrary non-privileged port
    print ("waiting on host %s port number %d"%(args.host,args.port)) 
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind((args.host, args.port))
    tcp.listen(1)
    conn, addr = tcp.accept()
    print ('Connected by', addr)
   
    s=Sounder()
    while s.sock:
        if not s.sock: break
        conn.send(s.get_nmea())
        time.sleep(args.interval)
    conn.close()


    """   x=s.get_value()
    if x:
            act,d,t,b =x
            #print x
            if act=="active":
                print "depth:",d,"m, temp:",t,"C, battery level:",b
            else:
                print "sounder inactive"
        else:
            print "problem"
            """
