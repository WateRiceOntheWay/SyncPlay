from typing import Union

import tornado.ioloop
import tornado.httpserver
import tornado.web
import requests
import json
import time
import threading

import msg_handler
from msg_handler import PodcastResponse, SyncRequest, DisconnectRequest, ConnectRequest,SyncResponse, PodcastRequest, ConnectResponse, DisconnectResponse,SerializedHandler

import wd
import free_port



class Server:

    class SpServerHandler(tornado.web.RequestHandler):

        def initialize(self, serialized_handler:SerializedHandler):
            self.serialized_handler = serialized_handler
        def post(self):
            data = tornado.escape.json_decode(self.request.body)
            ip = self.request.remote_ip
            print(ip)
            result = self.serialized_handler.handle(data,ip=ip)
            self.write(json.dumps(result))


    class SpServerInfo:
        def __init__(self,ip:str,port:int):
            self.ip = ip
            self.port = port
            self.connections = []

        def _do_add_connection(self,ip:str,port:int,username:str):
            self.connections.append({
                "ip": ip,
                "port": port,
                "username": username
            })

        def check_connectable(self,ip:str):
            for item in self.connections:
                if item["ip"] == ip:
                    return False
            return True

        def add_connection(self,ip:str,port:int,username:str):
            if self.check_connectable(ip):
                self._do_add_connection(ip,port,username)
                return True
            return False

        def remove_connection(self,ip:str):
            for item in self.connections:
                if item["ip"] == ip:
                    self.connections.remove(item)
                    return True
            return False

        def disconnect(self,ip:str):
            self.remove_connection(ip)

        def connect(self,ip:str,port:int,username:str):
            print(f"Connecting to {ip}:{port} as {username}.")
            return self.add_connection(ip,port,username)

        def podcast(self,sp_webdriver:wd.WD):
            for item in self.connections:
                ip = item["ip"]
                port = item["port"]
                username = item["username"]
                response = requests.post(f"http://{ip}:{port}",json=PodcastRequest(*sp_webdriver.get_state()).serialized())
                print(response.text)



    class SpServerMessageHandler(msg_handler.ServerMessageHandler):

        def __init__(self,sp_webdriver:wd.WD,sp_serverinfo:'Server.SpServerInfo'=None,**kwargs):
            super().__init__(**kwargs)
            """
            schema:
            [{
                "username": str,
                "ip": str,
                "port": int
            }]
            Only ip is used in comparing connections
            """

            self.sp_webdriver = sp_webdriver
            self.sp_serverinfo = sp_serverinfo


        def handle_connect_request(self, message: ConnectRequest, **kwargs):
            ip = kwargs["ip"]
            port = message.port
            username = message.username

            return message.generate_response(self.sp_serverinfo.connect(ip,port,username))

        def handle_disconnect_request(self, message: DisconnectRequest, **kwargs):
            ip = kwargs["ip"]
            self.sp_serverinfo.disconnect(ip)
            return message.generate_response()

        def handle_sync_request(self, message: SyncRequest, **kwargs):
            ip = kwargs["ip"]
            state = self.sp_webdriver.get_state()
            print(state,state[0].serialized())
            for item in self.sp_serverinfo.connections:
                if item["ip"] == ip:
                    # self.sp_webdriver.driver.switch_to.active_element

                    return message.generate_response(*self.sp_webdriver.get_state())
            return message.generate_response(wd.FormattedUrl.Void(),0,False)

        def handle_podcast_response(self, message: PodcastResponse, **kwargs):
            return message.generate_response()


    def __init__(self, port:int, sp_webdriver:wd.WD):
        self.server_thread = None
        self.port = port
        self.sp_webdriver = sp_webdriver
        self.sp_serverinfo = self.SpServerInfo("localhost",port)
        self.serialized_handler = SerializedHandler(Server.SpServerMessageHandler(sp_webdriver=self.sp_webdriver,sp_serverinfo=self.sp_serverinfo))
        self.application = tornado.web.Application([
            (r"/", self.SpServerHandler, {"serialized_handler": self.serialized_handler})
        ])

    def _start(self):
        self.application.listen(self.port)
        tornado.ioloop.IOLoop.current().start()


    def podcast(self):
        self.sp_serverinfo.podcast(self.sp_webdriver)

    def _stop(self):
        tornado.ioloop.IOLoop.current().add_callback(tornado.ioloop.IOLoop.current().stop)
        self.server_thread.join()


    def start(self):
        class sv_thrd(threading.Thread):
            def __init__(self,start_func,end_func):
                threading.Thread.__init__(self)
                self.start_func = start_func
                self.end_func = end_func

            def run(self):
                self.start_func()

            def stop(self):
                self.end_func()

        self.server_thread = sv_thrd(self._start,self._stop)
        self.server_thread.start()

    def stop(self):
        self.server_thread.stop()

def start_server(Wd:wd.WD,time_out:float = 2) -> Union[Server,None]:
    start_time = time.time()
    while time.time() - start_time < time_out:
        try:
            port = free_port.get_free_port()
            server = Server(port,Wd)
            server.start()
            return server
        except Exception as e:
            print(e)
            print("Retrying...")
            time.sleep(0.1)
    return None

if __name__ == "__main__":
    Wd = wd.WD()
    start_server(Wd)