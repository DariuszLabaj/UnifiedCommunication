from typing import Protocol


class ICommunication(Protocol):
    @property
    def Connected(self) -> bool:
        ...

    @property
    def Valid(self) -> bool:
        ...

    @property
    def LastUse(self) -> float:
        ...

    def connect(self) -> None:
        ...

    def setValidation(self, status: bool) -> None:
        ...

    def sendBytes(
        self, data: bytes, rcvSize: int = None, rcvTerminator: bytes = None
    ) -> bytes:
        ...

    def receiveBytes(self, size: int, rcvTerminator: bytes = None) -> bytes:
        ...

    def disconnect(self) -> None:
        ...
