import logging
import logging.config
import os
import sys

from toscaparser.tosca_template import ToscaTemplate


obj = ToscaTemplate("C:\\Users\\428430\\Downloads\\tosca templates data\\tosca templates data\\tosca_helloworld_invalid.yaml", None, True)
print obj.msg