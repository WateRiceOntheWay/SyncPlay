import logging

import tornado
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

class Client:
    class SpClientHandler(tornado.web.RequestHandler):

        def initialize(self, serialized_handler:SerializedHandler):
            self.serialized_handler = serialized_handler

        def post(self):
            data = tornado.escape.json_decode(self.request.body)
            result = self.serialized_handler.handle(data)
            self.write(json.dumps(result))


    class SpClientMessageHandler(msg_handler.ClientMessageHandler):

        def __init__(self, sp_webdriver: wd.WD, **kwargs):
            super().__init__(**kwargs)
            self.sp_webdriver = sp_webdriver

        def handle_sync_response(self, message: SyncResponse, **kwargs):
            print("Received a sync response.")
            self.sp_webdriver.sync_state(message.formatted_url, message.current_time, message.paused)
            return message.generate_response()

        def handle_podcast_request(self, message: PodcastRequest, **kwargs):
            print("Received a podcast request.")
            self.sp_webdriver.sync_state(message.formatted_url, message.current_time, message.paused)
            return message.generate_response()

        def handle_connect_response(self, message: ConnectResponse, **kwargs):
            print("Received a connect response.")
            return message.generate_response()

        def handle_disconnect_response(self, message: DisconnectResponse, **kwargs):
            print("Received a disconnect response.")
            return message.generate_response()



    def __init__(self, server_ip: str, server_port: int,username:str,local_port:int, sp_webdriver: wd.WD):
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username
        self.local_port = local_port

        self.sp_webdriver = sp_webdriver
        self.sp_client_message_handler = self.SpClientMessageHandler(sp_webdriver)
        self.serialized_handler = SerializedHandler(self.sp_client_message_handler)

        result = self.connect()
        if not result:
            raise Exception("Failed to connect to server.")

        self.application = tornado.web.Application([
            (r"/", self.SpClientHandler, {"serialized_handler": self.serialized_handler})
        ])


    def connect(self):
        response = requests.post(f"http://{self.server_ip}:{self.server_port}", json=ConnectRequest(self.username,self.local_port).serialized())
        self.serialized_handler.handle(response.json())
        print(response.json())
        return response.json()["accept"]

    def disconnect(self):
        response = requests.post(f"http://{self.server_ip}:{self.server_port}",
                                 json=DisconnectRequest().serialized())
        self.serialized_handler.handle(response.json())

    def sync(self):
        response = requests.post(f"http://{self.server_ip}:{self.server_port}",
                                 json=SyncRequest().serialized())
        print(response.json())
        self.serialized_handler.handle(response.json())

    def _start(self):
        self.application.listen(self.local_port)
        tornado.ioloop.IOLoop.current().start()

    # def start(self):
    #     self.server_thread = threading.Thread(target=self._start)
    #     self.server_thread.start()

    def _stop(self):
        self.disconnect()
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



def start_client(server_ip:str, server_port:int,username:str,sp_webdriver:wd.WD,time_out:float = 2):
    start_time = time.time()
    while time.time() - start_time < time_out:
        try:
            local_port = free_port.get_free_port()
            client = Client(server_ip,server_port,username,local_port,sp_webdriver)
            client.start()
            return client
        except Exception as e:
            logging.exception(e)
            print("Retrying...")

