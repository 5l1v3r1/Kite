
import socket
import threading

COMMAND_DISCOVER='-discover'
COMMAND_REPORT='-report'
COMMAND_UPDATE='-update'
COMMAND_UPLOAD='-upload'
DATA_LENGTH=1024
MULTICAST_ADDRESS=('255.255.255.255',12345)
MULTICAST_LOCAL_ADDRESS=('0.0.0.0',12345)
TCP_PORT=12346

class broadcast() :
    def __init__(self) :
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.bind(MULTICAST_LOCAL_ADDRESS)
        self.sock=sock

    def send(self,data) :
        mutex=threading.Lock()
        if mutex.acquire() :  #  TIPS : lock this for safe the buffer of send()
            self.sock.sendto(data,MULTICAST_ADDRESS)
            mutex.release()
        
    def recv(self) :
        data,addr=self.sock.recvfrom(DATA_LENGTH)
        return data

class packet() :
    def __init__(self) :
        self.is_master=False
        self.receiver_ip=''
        self.command=''
        
    def get_master(self) :
        if self.is_master :
            return True
        else :
            return False
        
    def set_master(self) :
        self.is_master=True
        
    def set_slave(self) :
        self.is_master=False
    
    def get_slave_receive_ip(self) :
        return self.receiver_ip
    
    def set_slave_receive_ip(self,data) :
        self.receiver_ip=data
        
    def get_slave_command(self) :
        return self.command
    
    def set_slave_command(self,command) :
        self.command=command
        
    def resolve(self,packet_data) :
        try :
            if packet_data[0]=='1' :
                self.is_master=True
            else :
                self.is_master=False
            receiver_ip_length=int(ord(packet_data[1]))
            if not receiver_ip_length==0 :
                self.receiver_ip=packet_data[2:2+receiver_ip_length-1]
            else :
                self.receiver_ip=''
            self.command=packet_data[2+receiver_ip_length:]
        except :
            print 'ERROR Packet!'
        
    def tostring(self) :
        packet_data=''
        if self.is_master :
            packet_data+='1'
        else :
            packet_data+='0'
        packet_data+=chr(len(self.receiver_ip))
        packet_data+=self.receiver_ip
        packet_data+=self.command
        return packet_data

def get_local_ip() :
    return socket.gethostbyname_ex(socket.gethostname())[2][0]  #  local machine ip ,not is VM machine ip
    
class distributed_master() :
    def __init__(self) :
        self.broadcast=broadcast()
        
    def __background_server_slave_thread(sock) :
        data=sock.recv()
        if data=='-update' :
            sock.send('{\'state\',\'OK!\'}')
        elif data=='-upload' :
            sock.send('OK')
        
    def __background_server_thread(self) :
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind(('',TCP_PORT))
        self.sock.listen(10)  #  support more fuzzing slave
        while True :
            client,client_address=self.sock.accept()
            client_thread=thread.Thread(target=self.__background_server_slave_thread,args=(client))
            client_thread.start()
    
    def __background_server_discover_thread(self) :
        while True :
            data=packet()
            data.resolve(self.broadcast.recv())
            if not data.get_master() :
                if data.get_slave_command()=='-discover' :
                    responed=packet()
                    responed.set_master()
                    responed.set_slave_command('')
                    self.send('-discover '+get_local_ip())
    
    def run(self) :
        self.trance_thread=threading.Thread(target=self.__background_server_slave_thread)
        self.trance_thread.start()
        self.discover_thread=threading.Thread(target=self.__background_server_discover_thread)
        self.discover_thread.start()
        
    def exit(self) :
        self.thread.stop()
    
    def send(self,data) :
        self.broadcast.send(data)
    
    def recv(self) :
        return self.broadcast.recv()
            
if __name__=='__main__' :
    distributed_master_=distributed_master()
    distributed_master_.run()
    while True :
#        print '->'
        command=input('->');
        if command=='-quit' :
            exit()  #  WARNING! Thread has no set demond
        send_data=packet()
        send_data.set_master()
        send_data.set_slave_command(command)
        distributed_master_.send(send_data.tostring())
    