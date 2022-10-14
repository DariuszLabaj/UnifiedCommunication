from dataclasses import dataclass
import time
from logging import Logger
from typing import Tuple
import serial

from UniCom.loggerHandling import loggerHandling


class GeneralSerial:
    @property
    def Connected(self) -> bool:
        self.__info.connected = self.__connection.is_open
        return self.__info.connected

    @property
    def LastUse(self) -> float:
        return self.__info.lastUse

    @dataclass
    class __deviceData:
        port: str
        baudRate: int
        byteSize: int
        parity: str
        stopBits: int
        xonXoff: int
        rtsCts: int
        eot: bytes

    @dataclass
    class __connectionInfo:
        timeout_s: float | None
        lastUse: float
        connected: bool = False

    def __init__(
        self,
        port: str,
        baudrate: int,
        bytesize: int = 8,
        parity=serial.PARITY_NONE,
        stopbits=1,
        xonxoff=0,
        rtscts=0,
        timeout: float = None,
        logger: Logger = None,
        eot: bytes = None,
    ):
        self.__device = GeneralSerial.__deviceData(
            port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, eot
        )
        self.__logger = logger
        self.__info = GeneralSerial.__connectionInfo(timeout, time.time())
        self.__connection = serial.Serial(
            port=self.__device.port,
            baudrate=self.__device.baudRate,
            bytesize=self.__device.byteSize,
            parity=self.__device.parity,
            stopbits=self.__device.stopBits,
            timeout=self.__info.timeout_s,
            xonxoff=self.__device.xonXoff,
            rtscts=self.__device.rtsCts,
        )

    def connect(self) -> None:
        self.__updateLastUse()
        try:
            if not self.Connected:
                self.__connection.open()
        except serial.SerialException as exception:
            loggerHandling(
                self, self.__logger, msg=f"Connect: {exception}, {self.__device}"
            )

    def __updateLastUse(self) -> None:
        self.__info.lastUse = time.time()

    def sendBytes(
        self,
        data: bytes,
        rcvSize: int = None,
        rcvTerminator: bytes = None,
        awaitReceive: float = 0,
    ) -> bytes:
        self.__updateLastUse()
        bytesToSend = (
            data + self.__device.eot if self.__device.eot is not None else data
        )
        dataSent = False
        bytesRecived = b""
        try:
            self.__connection.write(data)
            self.__connection.flush()
            dataSent = True
        except serial.SerialException as exception:
            self.disconnect()
            loggerHandling(self, self.__logger, msg=f"Send: {exception}, {bytesToSend}")
        if rcvSize and dataSent:
            if awaitReceive:
                time.sleep(awaitReceive)
            bytesRecived = self.receiveBytes(rcvSize, rcvTerminator)
        return bytesRecived

    def __getChunk(self, size: int) -> Tuple[bool, bytes]:
        data = b""
        status = False
        try:
            data = self.__connection.read(size)
            status = True
        except serial.SerialException as exception:
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
            bytesRecived = GeneralSerial.__trimDataToTerminator(
                bytesRecived, rcvTerminator
            )
        else:
            _, rcvData = self.__getChunk(size)
            bytesRecived = rcvData
        return bytesRecived

    def disconnect(self) -> None:
        self.__connection.close()
