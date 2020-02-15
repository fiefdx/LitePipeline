# -*- coding: UTF-8 -*-

class SingleTone(object):
    __instance = None

    def __new__(cls, val, val2 = "test"):
        if SingleTone.__instance is None:
            SingleTone.__instance = object.__new__(cls)
        SingleTone.__instance.val = val
        return SingleTone.__instance

    def __init__(self, val, val2):
        self.val = False
        self.val2 = val
        self.val3 = val2


print(SingleTone("a"))
print(SingleTone("b"))
