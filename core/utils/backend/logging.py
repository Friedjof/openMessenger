# Friedjof Noweck
# 20.08.2021 Fr
import uuid
from datetime import datetime
from colorama import Fore, Back, Style


class LoggingStatus:
    class DEBUG:
        status: int = -1
        msg: str = "DEBUG     "

    class SUCCESSFUL:
        status: int = 0
        msg: str = "SUCCESSFUL"

    class INFO:
        status: int = 1
        msg: str = "INFO      "

    class WARNING:
        status: int = 2
        msg: str = "WARNING   "

    class ERROR:
        status: int = 3
        msg: str = "ERROR     "

    class CRITICAL:
        status: int = 4
        msg: str = "CRITICAL  "


class Logging:
    def __init__(
            self, logLevel: LoggingStatus.__dict__ = LoggingStatus.DEBUG,
            configuration: object = None,
            logFormat: str = "{time}; {status} | {msg}",
            lineFormat: str = "{time}; {status} |{msg}",
            consoleLogging: bool = True, timeFormat: str = "%Y-%m-%d, %H:%M:%S.%f"
    ):
        self._config = configuration
        self._logLevel = logLevel
        self._logFormat = logFormat
        self._lineFormat = lineFormat
        self._consoleLogging = consoleLogging
        self._timeFormat = timeFormat

    def log(self, status: LoggingStatus.__dict__, msg: str = None,
            end: str = "\n", ignore: bool = False,
            line: bool = False, lineString: str = "-", lineSize: int = 64,
            background: Back = None, foreground: Fore = None, style: Style = Style.NORMAL):
        if not ignore:
            if background is None:
                if status.status == LoggingStatus.DEBUG.status:
                    background: Back = Back.LIGHTYELLOW_EX
                elif status.status == LoggingStatus.SUCCESSFUL.status:
                    background: Back = Back.GREEN
                elif status.status == LoggingStatus.INFO.status:
                    if line:
                        background: Back = Back.WHITE
                    else:
                        background: Back = Back.RESET
                elif status.status == LoggingStatus.WARNING.status:
                    background: Back = Back.YELLOW
                elif status.status == LoggingStatus.ERROR.status:
                    background: Back = Back.BLACK
                elif status.status == LoggingStatus.CRITICAL.status:
                    background: Back = Back.LIGHTRED_EX
                else:
                    background: Back = Back.RESET

            if foreground is None:
                if status.status == LoggingStatus.DEBUG.status:
                    foreground: Fore = Fore.BLACK
                elif status.status == LoggingStatus.SUCCESSFUL.status:
                    foreground: Fore = Fore.BLACK
                elif status.status == LoggingStatus.INFO.status:
                    if line:
                        foreground: Fore = Fore.BLACK
                    else:
                        foreground: Fore = Fore.RESET
                elif status.status == LoggingStatus.WARNING.status:
                    foreground: Fore = Fore.BLACK
                elif status.status == LoggingStatus.ERROR.status:
                    foreground: Fore = Fore.LIGHTRED_EX
                elif status.status == LoggingStatus.CRITICAL.status:
                    foreground: Fore = Fore.BLACK
                else:
                    foreground: Fore = Fore.RESET

            if style == Style.NORMAL:
                if status.status == LoggingStatus.DEBUG.status:
                    style: Style = Style.BRIGHT
                elif status.status == LoggingStatus.SUCCESSFUL.status:
                    style: Style = Style.BRIGHT
                elif status.status == LoggingStatus.INFO.status:
                    style: Style = Style.DIM
                elif status.status == LoggingStatus.WARNING.status:
                    style: Style = Style.NORMAL
                elif status.status == LoggingStatus.ERROR.status:
                    style: Style = Style.BRIGHT
                elif status.status == LoggingStatus.CRITICAL.status:
                    style: Style = Style.BRIGHT
                else:
                    style: Style = Style.NORMAL

            log_message = background + foreground + style + (self._lineFormat if line else self._logFormat)

            if line:
                if msg is not None:
                    msg = lineString * int((lineSize - len(msg) - 4) / 2 / len(lineString)) + '> ' + msg + ' <' + lineString[::-1] * int(
                        (lineSize - len(msg) - 4) / 2 / len(lineString))
                    if ((lineSize - len(msg) - 4) / 2) % 2 != 1:
                        msg += lineString[::-1][0]
                else:
                    msg = lineString * lineSize
                print(
                    log_message.format(
                        time=datetime.now().strftime(self._timeFormat),
                        status=status.msg,
                        msg=msg
                    ), end=end
                )
            elif self._consoleLogging and status.status >= self._logLevel.status:
                print(
                    log_message.format(
                        time=datetime.now().strftime(self._timeFormat),
                        status=status.msg, msg=msg
                    ), end=end
                )


# Logging Example
if __name__ == "__main__":
    logger = Logging()
    logger.log(LoggingStatus.DEBUG, msg=uuid.uuid4().hex)
    logger.log(LoggingStatus.INFO, msg=uuid.uuid4().hex)
    logger.log(LoggingStatus.INFO, msg=uuid.uuid4().hex, line=True)
    logger.log(LoggingStatus.INFO, msg=uuid.uuid4().hex, line=True, lineString="~", lineSize=64)
    logger.log(LoggingStatus.WARNING, msg=uuid.uuid4().hex)
    logger.log(LoggingStatus.ERROR, msg=uuid.uuid4().hex)
    logger.log(LoggingStatus.CRITICAL, msg=uuid.uuid4().hex)
