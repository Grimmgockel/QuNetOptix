from qns.entity.node.app import Application
from qns.entity.node import QNode
from qns.network.requests import Request

from typing import List

'''
QNode with knowledge over vlink requests
'''
class VLAwareQNode(QNode):
    def __init__(self, name: str = None, apps: List[Application] = None):
        super().__init__(name, apps)
        self.vlinks: List[Request] = []

    def add_vlink(self, vlink: Request):
        self.vlinks.append(vlink)