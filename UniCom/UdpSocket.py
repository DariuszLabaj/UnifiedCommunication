from logging import Logger
import socket
from UniCom.GeneralSocket import GeneralSocket


class UdpSocket(GeneralSocket):
    def __init__(
        self,
        ip: str,
        port: int,
        timeout: float = None,
        logger: Logger = None,
        eot: bytes = None,
    ):
        super().__init__(
            ip, port, socket.AF_INET, socket.SOCK_DGRAM, timeout, logger, eot
        )
