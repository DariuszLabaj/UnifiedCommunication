from logging import Logger


def loggerHandling(self: object, logger: Logger | None, msg: str = None) -> None:
    issue = f"EXCEPTION in {type(self).__name__}"
    if msg:
        issue += f", {msg}"
    if logger:
        logger.exception(issue + "\n")
    else:
        print(issue)
