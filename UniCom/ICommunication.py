from typing import Protocol


class ICommunication(Protocol):
    @property
    def Connected(self) -> bool:
        ...

    @property
    def LastUse(self) -> float:
        ...

    def connect(self) -> None:
        ...

    def sendBytes(
        self,
        data: bytes,
        rcvSize: int = None,
        rcvTerminator: bytes = None,
        awaitReceive: float = 0,
    ) -> bytes:
        ...

    def receiveBytes(self, size: int, rcvTerminator: bytes = None) -> bytes:
        ...

    def disconnect(self) -> None:
        ...
