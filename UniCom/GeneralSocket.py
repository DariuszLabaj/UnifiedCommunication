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
    def Valid(self) -> bool:
        return self.__info.dataValid

    @property
    def LastUse(self) -> float:
        return self.__info.lastUse

    @dataclass(slots=True)
    class __deviceData:
        ip: str
        port: int
        eot: bytes | None

        def __str__(self) -> str:
            return f"{self.ip}:{self.port}"

    @dataclass(slots=True)
    class __connectionInfo:
        timeout_s: float | None
        lastUse: float
        connected: bool = False
        dataValid: bool = False

    def __init__(
        self,
        ip: str,
        port: int,
        addressFamily: socket.AddressFamily,
        socketKind: socket.SocketKind,
        timeout_s: float = None,
        logger: Logger = None,
        eot: bytes = None,
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
            self.__connection.connect(self.__device)
            self.__info.connected = True
            self.setValidation(True)
        except socket.error as exception:
            loggerHandling(self, self.__logger, msg=f"Connect: {exception}, {self.__device}")
            self.__info.connected = True

    def setValidation(self, status: bool) -> None:
        self.__info.dataValid = status

    def __updateLastUse(self) -> None:
        self.__info.lastUse = time.time()

    def sendBytes(
        self, data: bytes, rcvSize: int = None, rcvTerminator: bytes = None
    ) -> bytes:
        self.__updateLastUse()
        bytesToSend = data + self.__device.eot if self.__device.eot else data
        dataSent = False
        bytesRecived = b""
        try:
            self.__connection.send(data)
            dataSent = True
        except socket.error as exception:
            self.disconnect()
            loggerHandling(self, self.__logger, msg=f"Send: {exception}, {bytesToSend}")
        if rcvSize and dataSent:
            bytesRecived = self.receiveBytes(rcvSize, rcvTerminator)
        return bytesRecived

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
        terminatorPosition = data.index(terminator)
        terminatorLen = len(terminator)
        if terminatorPosition < terminatorLen:
            terminatorPosition = data[terminatorLen:].index(terminator) + terminatorLen
        return data[:terminatorPosition]

    def receiveBytes(self, size: int, rcvTerminator: bytes = None) -> bytes:
        bytesRecived = b""
        if rcvTerminator is not None:
            while rcvTerminator not in bytesRecived:
                rcvStatus, rcvData = self.__getChunk(size)
                if not rcvStatus:
                    break
                bytesRecived += rcvData
            bytesRecived = GeneralSocket.__trimDataToTerminator(bytesRecived, rcvTerminator)
        else:
            _, rcvData = self.__getChunk(size)
            bytesRecived = rcvData
        return bytesRecived

    def disconnect(self) -> None:
        self.setValidation(False)
        self.__connection.close()
        self.__info.connected = False
