from wd import *
from abc import abstractmethod


class Message:
    def __init__(self):
        self.type = None

    @abstractmethod
    def serialized(self, **kwargs):
        pass

    @abstractmethod
    def generate_response(self,**kwargs):
        pass


class VoidResponse(Message):
    """
    A void response message. It is only used as a generate_response method return value, for those that do not need a meaningful response.
    VoidResponse cannot be a parameter of handle method in MessageHandler.
    """

    def __init__(self):
        super().__init__()

    def serialized(self):
        return {
            "type": "void-response"
        }

    def generate_response(self):
        return None


class ConnectResponse(Message):
    def __init__(self, accept=False):
        super().__init__()
        self.type = 'connect-response'
        self.accept = accept

    def set(self, accept):
        self.accept = accept

    def serialized(self):
        return {
            "type": self.type,
            "accept": self.accept
        }

    def generate_response(self):
        return VoidResponse()


class ConnectRequest(Message):
    def __init__(self, username: str = None, port: int = None):
        super().__init__()
        self.type = 'connect-request'
        self.username = username
        self.port = port

    def set(self, username=None, port=None):
        self.username = username if username is not None else self.username
        self.port = port if port is not None else self.port

    def serialized(self):
        if self.username is None:
            raise Exception("username is None")
        if self.port is None:
            raise Exception("port is None")

        return {
            "type": self.type,
            "username": self.username,
            "port": self.port
        }

    def generate_response(self, accept=False):
        return ConnectResponse(accept)


class DisconnectResponse(Message):
    def __init__(self):
        super().__init__()
        self.type = 'disconnect-response'

    def serialized(self):
        return {
            "type": self.type
        }

    def generate_response(self):
        return VoidResponse()


class DisconnectRequest(Message):
    def __init__(self, username=None):
        super().__init__()
        self.type = 'disconnect-request'
        self.username = username

    def set(self, username):
        self.username = username

    def serialized(self):
        if self.username is None:
            raise Exception("username is None")
        return {
            "type": self.type
        }

    def generate_response(self):
        return DisconnectResponse()


class SyncResponse(Message):
    def __init__(self, formattedd_url: FormattedUrl, current_time: float, paused: bool):
        super().__init__()
        self.type = 'sync-response'
        self.formatted_url = formattedd_url
        self.current_time = current_time
        self.paused = paused

    def set(self, formatted_url: FormattedUrl = None, current_time: float = None, paused: bool = None):
        self.formatted_url = formatted_url if formatted_url is not None else self.formatted_url
        self.current_time = current_time if current_time is not None else self.current_time
        self.paused = paused if paused is not None else self.paused

    def serialized(self):
        if self.formatted_url is None or self.current_time is None or self.paused is None:
            raise Exception("formatted_url, current_time or paused is None")
        return {
            "type": self.type,
            "formatted_url": self.formatted_url.serialized(),
            "current_time": self.current_time,
            "paused": self.paused
        }

    def generate_response(self):
        return VoidResponse()


class SyncRequest(Message):
    def __init__(self):
        super().__init__()
        self.type = 'sync-request'

    def serialized(self):
        return {
            "type": self.type
        }

    def generate_response(self, formatted_url: FormattedUrl, current_time: float, paused: bool):
        return SyncResponse(formatted_url, current_time, paused)


class PodcastResponse(Message):
    def __init__(self, accept=False):
        super().__init__()
        self.type = 'podcast-response'
        self.accept = accept

    def set(self, accept):
        self.accept = accept

    def serialized(self):
        return {
            "type": self.type,
            "accept": self.accept
        }

    def generate_response(self):
        return VoidResponse()


class PodcastRequest(Message):
    def __init__(self, formatted_url: FormattedUrl, current_time: float, paused: bool):
        super().__init__()
        self.type = 'podcast-request'
        self.formatted_url = formatted_url
        self.current_time = current_time
        self.paused = paused

    def set(self, formatted_url: FormattedUrl = None, current_time: float = None, paused: bool = None):
        self.formatted_url = formatted_url if formatted_url is not None else self.formatted_url
        self.current_time = current_time if current_time is not None else self.current_time
        self.paused = paused if paused is not None else self.paused

    def serialized(self):
        if self.formatted_url is None or self.current_time is None or self.paused is None:
            raise Exception("formatted_url, current_time or paused is None")
        return {
            "type": self.type,
            "formatted_url": self.formatted_url.serialized(),
            "current_time": self.current_time,
            "paused": self.paused
        }

    def generate_response(self, accept=False):
        return PodcastResponse(accept)


def from_serialized(serialized: dict) -> Message:
    if 'type' not in serialized:
        raise Exception("Unacceptable message format.")
    type = serialized['type']
    if type == 'connect-request':
        return ConnectRequest(serialized['username'], serialized['port'])
    elif type == 'connect-response':
        return ConnectResponse(serialized['accept'])
    elif type == 'disconnect-request':
        return DisconnectRequest(serialized['username'])
    elif type == 'disconnect-response':
        return DisconnectResponse()
    elif type == 'sync-request':
        return SyncRequest()
    elif type == 'sync-response':
        return SyncResponse(FormattedUrl.from_serialized(serialized['formatted_url']), serialized['current_time'], serialized['paused'])
    elif type == 'podcast-request':
        return PodcastRequest(FormattedUrl.from_serialized(serialized['formatted_url']), serialized['current_time'],
                              serialized['paused'])
    elif type == 'podcast-response':
        return PodcastResponse(serialized['accept'])
    else:
        raise Exception("Unknown message type")


def to_serialized(Message) -> dict:
    return Message.serialized()


def is_server_message(message: Message):
    """
    Check if the message is sent to a server, from a client.
    :param message: Message
    :return: bool
    """

    return message.type in ['connect-request', 'disconnect-request', 'sync-request', 'podcast-response']


def is_client_message(message: Message):
    """
    Check if the message is sent to a client, from a server.
    :param message:
    :return:
    """
    return message.type in ['connect-response', 'disconnect-response', 'sync-response', 'podcast-request']


class MessageHandler:

    def __init__(self, **kwargs):
        self.args = kwargs

    @abstractmethod
    def handle(self, message: Message, **kwargs) -> Message:
        """
        Handle the message.
        This function should be called in tornado.web.RequestHandler post method. It classifies the message type and calls the appropriate handler.
        :param message: A message object.
        :return: A Message object, which is a response to the message.
        """
        pass


class ServerMessageHandler(MessageHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle(self, message: Message, **kwargs) -> Message:

        # print(message.serialized())

        if message.type == 'connect-request':
            return self.handle_connect_request(message, **kwargs)
        elif message.type == 'disconnect-request':
            return self.handle_disconnect_request(message, **kwargs)
        elif message.type == 'sync-request':
            return self.handle_sync_request(message, **kwargs)
        elif message.type == 'podcast-response':
            return self.handle_podcast_response(message, **kwargs)
        else:
            raise Exception("Unknown message type")

    @abstractmethod
    def handle_connect_request(self, message: ConnectRequest, **kwargs):
        """
        Handle the ConnectRequest message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_disconnect_request(self, message: DisconnectRequest, **kwargs):
        """
        Handle the DisconnectRequest message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_sync_request(self, message: SyncRequest, **kwargs):
        """
        Handle the SyncRequest message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_podcast_response(self, message: PodcastResponse, **kwargs):
        """
        Handle the PodcastResponse message.
        :param message:
        :return:
        """
        pass


class ClientMessageHandler(MessageHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle(self, message: Message, **kwargs) -> Message:

        # print(message.serialized())

        if message.type == 'connect-response':
            return self.handle_connect_response(message, **kwargs)
        elif message.type == 'disconnect-response':
            return self.handle_disconnect_response(message, **kwargs)
        elif message.type == 'sync-response':
            return self.handle_sync_response(message, **kwargs)
        elif message.type == 'podcast-request':
            return self.handle_podcast_request(message, **kwargs)
        else:
            raise Exception("Unknown message type")

    @abstractmethod
    def handle_connect_response(self, message: ConnectResponse, **kwargs):
        """
        Handle the ConnectResponse message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_disconnect_response(self, message: DisconnectResponse, **kwargs):
        """
        Handle the DisconnectResponse message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_sync_response(self, message: SyncResponse, **kwargs):
        """
        Handle the SyncResponse message.
        :param message:
        :return:
        """
        pass

    @abstractmethod
    def handle_podcast_request(self, message: PodcastRequest, **kwargs):
        """
        Handle the PodcastRequest message.
        :param message:
        :return:
        """
        pass


class SerializedHandler:

    def __init__(self, message_handler: MessageHandler):
        self.message_handler = message_handler

    def handle(self, serialized: dict, **kwargs) -> dict:
        message = from_serialized(serialized)
        response = self.message_handler.handle(message, **kwargs)
        return to_serialized(response)
