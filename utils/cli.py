import logging

import tornado

import client,server,wd,msg_handler
import threading

import json
import os

class Cli:

    def _output(self,message:str,end = "\n"):
        print(f"<{'/'.join(self.page_seq)}> {message}",end = end)
    def _input(self,hint=">>>"):
        return input(f"{hint} ")

    def _interact(self,message:str,end="\n",hint=">>>"):
        self._output(message,end = end)
        return self._input(hint=hint)

    def _start_server(self):
        self.server = server.start_server(self.Wd)
        if self.server is None:
            self._output("Failed to start server.")
            return False
        self._output(f"Server started on port {self.server.port}.")
        return True

    def _end_server(self):
        if self.server:
            self.server.stop()
            self._output("Server stopped.")
            self.server = None  # 清除引用
        return True

    def _start_client(self):
        ip = self._interact("Server IP:")
        port = int(self._interact("Server port:"))
        username = self._interact("Username:")
        self.client = client.start_client(ip,port,username,self.Wd)
        if self.client is None:
            self._output(f"Failed to start client. Please check the server ip and port.\nIP:\"{ip}\" Port:\"{port}\"")
            return False

        self._output(f"Client started on port {self.client.local_port}.")
        return True

    def _end_client(self):
        if self.client:
            self.client.stop()
            self._output("Client stopped.")
            self.client = None  # 清除引用
        return True


    def _print_page(self):
        self._output(f"{self.cli_infor['body'][self.page_seq[-1]]['index']}")

    def _print_head(self):
        print(f"{self.cli_infor['head']['title']}\n{self.cli_infor['head']['description']}")

    def _print_help(self):
        self._output(f"{self.cli_infor['body'][self.page_seq[-1]]['help']}")

    def _parse_command(self,command):
        if command in ["h", "help"]:
            self._print_help()
            return True
        elif command in ["q", "quit",".."]:
            self.page_seq = self.page_seq[:-1]
            return True
        else:
            if self.page_seq[-1] == "sync_play":
                if command in ["s","server"]:
                    if self._start_server():
                        self.page_seq.append("server")
                        self._print_page()
                    return True
                elif command in ["c","client"]:
                    if self._start_client():
                        self.page_seq.append("client")
                        self._print_page()
                    return True

            if self.page_seq[-1] == "server":
                if command in ["q","quit",".."]:
                    if self._end_server():
                        self.page_seq = self.page_seq[:-1]
                        self._print_page()
                    return True
                elif command in ["p","podcast"]:
                    self.server.podcast()
                    return True
            if self.page_seq[-1] == "client":
                if command in ["q","quit",".."]:
                    if self._end_client():
                        self.page_seq = self.page_seq[:-1]
                        self._print_page()
                    return True
                elif command in ["s","sync"]:
                    self.client.sync()
                    return True
            return False



    def _start(self):
        self._print_head()
        self.page_seq = ["sync_play"]
        self._print_page()
        while True:
            command = self._interact(message="",end="",hint=">>>")
            if not self._parse_command(command):
                self._output("Invalid command. Type \"h\" or \"help\" for help.")
            if len(self.page_seq) == 0:
                self.Wd.driver.quit()
                tornado.ioloop.IOLoop.current().add_callback(tornado.ioloop.IOLoop.current().stop)
                tornado.ioloop.IOLoop.current().stop()
                print("Terminating SyncPlay ...")
                break





    def __init__(self):
        self.cli_infor = json.load(open(os.path.join(__file__,"..","cli.json")))
        self.Wd = wd.WD()
        self.page_seq = []
        self.server = None
        self.client = None
        self._start()

if __name__=="__main__":
    Cli()
    for thread in threading.enumerate():
        if thread is not threading.main_thread():
            thread.join(timeout=5)  # 等待线程结束

    os._exit(0)