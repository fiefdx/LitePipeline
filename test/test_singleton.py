# -*- coding: UTF-8 -*-

class SingleTone(object):
    __instance = None

    def __new__(cls, val):
        if SingleTone.__instance is None:
            SingleTone.__instance = object.__new__(cls)
        SingleTone.__instance.val = val
        return SingleTone.__instance


print(SingleTone("a"))
print(SingleTone("b"))
