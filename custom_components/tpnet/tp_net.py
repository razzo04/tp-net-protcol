from ast import While
import asyncio
import datetime
from enum import StrEnum
import logging
from homeassistant.core import HomeAssistant
from dataclasses import dataclass
from typing import cast
from homeassistant.config_entries import ConfigEntry


from .aioudpy import open_remote_endpoint, Endpoint, RemoteEndpoint

class TypeMessage(StrEnum): 
    SYSTEM = "SYSTEM"
    GET = "GET"
    SET = "SET"
    INC = "INC"
    DEC = "DEC"
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBCRIBE"
    DATA = "DATA"
    ERROR = "ERROR"

class Model(StrEnum):
    NXA = "NXA"
    NZA = "NZA"

presetnumber = {Model.NXA: 5}

_LOGGER = logging.getLogger(__name__)


MAX_TIMEOUT = datetime.timedelta(seconds=10)

@dataclass
class Message:
    type: TypeMessage
    paramsList: list[str]
    
    MAX_PARAM = 4

    def dump(self):
        string =  f'{self.type} ' + ' '.join(self.paramsList) + "\n"

        return string.encode()
    @classmethod
    def load(cls, data: str):
        split_data = data.split(" ")
        message_type = TypeMessage[split_data[0]]
        return cls(message_type, split_data[1:])


PORT = 5800
def done_callback(future):
    try:
        result = future.result()
    except Exception as exc:
        _LOGGER.exception("exception during listening ", exc)

class TpNet: 
    def __init__(self,hass: HomeAssistant, host: str) -> None:
        self.host = host
        self._hass = hass
        self._model: Model = None
        self._connection: RemoteEndpoint = None
        self.available = False
        self._listen_task = None
        self._check_ping_task = None

        self.last_ping: datetime.datetime = None

        self._future_list: dict[str, asyncio.Future[Message]] = {}

        self.data: dict[str, list[str]] = {}

    async def listen(self):
        while True:
            data = await self._connection.receive()

            data = cast(bytes, data)
            _LOGGER.debug(f"recived message {data}") 

            for message_raw in data.decode("ASCII").split("\n"):
                if not message_raw:
                    continue
                # _LOGGER.debug(f"message to process {message_raw}") 
                message = Message.load(message_raw)

                if message.type == TypeMessage.DATA:
                    future = self._future_list.get(message.paramsList[0], None)
                    if future:
                        future.set_result(message)
                        self._future_list[message.paramsList[0]] = None

                    self.data[message.paramsList[0]] = message.paramsList[1:]
                if message.type == TypeMessage.SYSTEM and message.paramsList[0] == "PING":
                    self.last_ping = datetime.datetime.now()
                    self.available = True
                    _LOGGER.debug("sending response to ping")

                    await self.send(Message(TypeMessage.SYSTEM,["PONG"]))

                    # handle message

    async def check_ping_time(self):
        while True:
            if self.available and (self.last_ping == None or (datetime.datetime.now() - self.last_ping) > MAX_TIMEOUT):
                self.available = False
                _LOGGER.warning("not message from deveice")
            await asyncio.sleep(5)


    def close(self):
        self._connection.abort()

    async def connect(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""        
        
        result = await self.start_listening()

        if not result:
            return False
        message = await self.get(["POWER"])
            
        self.available = message != None

        if self.available:
           
            if self._check_ping_task:
                self._check_ping_task.cancel()
                self._check_ping_task = None
            self._check_ping_task = asyncio.create_task(self.check_ping_time())

        return self.available

    async def start_listening(self) -> bool:
        if not self._connection._closed:
            self._connection.abort()
        try:
            self._connection = await open_remote_endpoint(self.host, PORT)

        except ConnectionRefusedError as err:
            return False 

        self._listen_task = self._hass.async_create_background_task(self.listen(), name="Listen")
        self._listen_task.add_done_callback(done_callback)
        return True
    
    async def get(self, params: list[str]) -> Message | None:
        hasfuture = self._future_list.get(params[0]) != None



        if not hasfuture:
            future = asyncio.get_event_loop().create_future()


            self._future_list[params[0]] = future
        else:
            future = self._future_list[params[0]]


        await self.send(Message(TypeMessage.GET, params))
        _LOGGER.debug("start to wait for get event")
        try:
            async with asyncio.timeout(1):
                message = await future
            
            return message

        except TimeoutError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            _LOGGER.debug(f"get request for {params} timeout")
            self._future_list[params[0]] = None
            
            return None

    async def turn_on(self):
        await self.set(["POWER","ON"])
    
    async def turn_off(self):
        await self.set(["POWER","OFF"])
    
    async def set(self, params: list[str]):
        await self.send(Message(TypeMessage.SET, params))

    async def send(self, message: Message):
        if not self.available:
            self._connection.send(Message(TypeMessage.SYSTEM,["CONNECT","PINGPONG"]).dump())
        self._connection.send(message.dump())

    async def get_all(self):
        await self.send(Message(TypeMessage.GET, ["ALL"]))

    def __del__(self):
        self.close()
    


    


        
