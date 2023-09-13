from dataclasses import dataclass
from logging import Logger
import socket
import time
from typing import Tuple

from UniCom.loggerHandling import loggerHandling


class GeneralSocket:
    @property
    def Connected(self) -> bool:
        return self.__info.connected

    @property
    def LastUse(self) -> float:
        return self.__info.lastUse

    @dataclass(slots=True)
    class __deviceData:
        ip: str
        port: int
        eot: bytes | None

        def get(self):
            return self.ip, self.port

        def __str__(self) -> str:
            return f"{self.ip}:{self.port}"

    @dataclass(slots=True)
    class __connectionInfo:
        timeout_s: float | None
        lastUse: float
        connected: bool = False

    def __init__(
        self,
        ip: str,
        port: int,
        addressFamily: socket.AddressFamily,
        socketKind: socket.SocketKind,
        timeout_s: float | None = None,
        logger: Logger | None = None,
        eot: bytes | None = None,
    ):
        self.__device = GeneralSocket.__deviceData(ip, port, eot)
        self.__logger = logger
        self.__info = GeneralSocket.__connectionInfo(timeout_s, time.time())
        self.__connection = socket.socket(addressFamily, socketKind)

    def connect(self) -> None:
        self.__updateLastUse()
        if self.__info.timeout_s:
            self.__connection.settimeout(self.__info.timeout_s)
        try:
            self.__connection.connect(self.__device.get())
            self.__info.connected = True
        except socket.error as exception:
            loggerHandling(
                self, self.__logger, msg=f"Connect: {exception}, {self.__device}"
            )
            self.__info.connected = False

    def __updateLastUse(self) -> None:
        self.__info.lastUse = time.time()

    def sendBytes(
        self,
        data: bytes,
        rcvSize: int | None = None,
        rcvTerminator: bytes | None = None,
        awaitReceive: float = 0,
    ) -> bytes:
        self.__updateLastUse()
        bytesToSend = (
            data + self.__device.eot if self.__device.eot is not None else data
        )
        dataSent = False
        bytesReceived = b""
        try:
            self.__connection.send(data)
            dataSent = True
        except socket.error as exception:
            self.disconnect()
            loggerHandling(self, self.__logger, msg=f"Send: {exception}, {bytesToSend}")
        if rcvSize and dataSent:
            if awaitReceive:
                time.sleep(awaitReceive)
            bytesReceived = self.receiveBytes(rcvSize, rcvTerminator)
        return bytesReceived

    def __getChunk(self, size: int) -> Tuple[bool, bytes]:
        data = b""
        status = False
        try:
            data = self.__connection.recv(size)
            status = True
        except socket.error as exception:
            self.disconnect()
            loggerHandling(self, self.__logger, msg=f"Receive: {exception}, {data}")
        finally:
            return status, data

    @staticmethod
    def __trimDataToTerminator(data: bytes, terminator: bytes) -> bytes:
        terminatorPosition = data.rfind(terminator)
        return data[:terminatorPosition]

    def receiveBytes(self, size: int, rcvTerminator: bytes | None = None) -> bytes:
        bytesReceived = b""
        if rcvTerminator is not None:
            while rcvTerminator not in bytesReceived:
                rcvStatus, rcvData = self.__getChunk(size)
                if not rcvStatus:
                    break
                bytesReceived += rcvData
            bytesReceived = GeneralSocket.__trimDataToTerminator(
                bytesReceived, rcvTerminator
            )
        else:
            _, rcvData = self.__getChunk(size)
            bytesReceived = rcvData
        return bytesReceived

    def disconnect(self) -> None:
        self.__connection.close()
        self.__info.connected = False
