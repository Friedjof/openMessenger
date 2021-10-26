# Friedjof Noweck
# 18.08.2021 Mi
import socket
import ssl

from core.utils.backend.configuration import Configuration
from core.utils.backend.request import Request, RequestTypes, RequestStatus
from core.utils.backend.logging import LoggingStatus

from server.backend.utils.requestEvaluation import Evaluation


class Server:
    def __init__(self, host: str = '127.0.0.1', port: int = 34911):
        self.port = port
        self.host = host

        self.config = Configuration(logLevel=LoggingStatus.DEBUG).load()
        self.serverEvaluation = Evaluation(configuration=self.config)

    def mainloop(self, buf: int = 10240):
        self.config.log.log(
            self.config.logStatus.INFO,
            msg="Server is started", line=True)
        self.config.log.log(self.config.logStatus.INFO, f"Host: {self.host}; Port: {self.port}")
        try:
            while True:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind((self.host, self.port))
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.load_cert_chain(
                        self.config.conf.socket["ssl"]["pem"],
                        self.config.conf.socket["ssl"]["key"]
                    )
                    sock.listen(2)
                    with context.wrap_socket(sock, server_side=True) as ssock:
                        conn, addr = ssock.accept()
                        self.config.log.log(
                            self.config.logStatus.INFO,
                            msg=f"Connection from {addr[0]}",
                            line=True, lineString="-"
                        )
                        while True:
                            data = conn.recv(buf)
                            if not data:
                                conn.close()
                                break
                            request: Request = Request(payload=data)
                            response: Request = self.serverEvaluation.load(request=request)
                            conn.sendall(response.as_pickle())
                        conn.close()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    s = Server(host='127.0.0.1', port=34911)
    s.mainloop()
