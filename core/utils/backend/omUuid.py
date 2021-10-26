# Friedjof Noweck
# 21.08.2021 Sa

import uuid


class UUID:
    def __init__(self):
        self.generate = lambda: uuid.uuid4().hex
