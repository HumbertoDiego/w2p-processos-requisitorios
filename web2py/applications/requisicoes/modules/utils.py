#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *

def mk_popoverhtml(id_popover, mystyle="", botao=""):
    html= """
<div id="%s" class="popover popover-x popover-default">
<div class="arrow"></div>
<textarea class="popover-body popover-content form-control" style="%s"></textarea>
<div class="popover-footer">
    <button class="btn btn-secondary" data-label="Cancelar" data-dismiss="popover-x"></span>&nbsp;Cancelar</button>
    %s
    <button class="btn btn-primary" data-label="OK" onclick="replace(this)" data-dismiss="popover-x"><span class="fa fa-check"></span>&nbsp;OK</button>
</div>
</div>
"""%(id_popover+"_popover",mystyle,botao)
    return XML(html)
