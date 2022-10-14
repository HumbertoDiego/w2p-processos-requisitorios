#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *

def posto_graduacao(cod_posto_grad, descricao_e_abreviatura=1):
    """Funcao para retornar a abreviatura do posto, a descricao ou ambas.
    Argumentos: 
    Onde: (posto_grad => inteiro que corresponde a um posto ou graduação)
            (descricao_e_abreviatura => inteiro_tipo_dado_retornar => 
                1 para so abreviatura,
                2 para so descrição ou 
                3 para ambos
    """
    abreviatura = ""
    descricao = ""
    #   Exército
    if cod_posto_grad == 1:
        descricao = 'Marechal'
        abreviatura = 'Mar'
    elif cod_posto_grad == 2:
        descricao = 'General de Exército'
        abreviatura = 'Gen Ex'
    elif cod_posto_grad == 3:
        descricao = 'General de Divisão'
        abreviatura = 'Gen Div'
    elif cod_posto_grad == 4:
        descricao = 'General de Brigada'
        abreviatura = 'Gen Bda'
    elif cod_posto_grad == 5:
        descricao = 'Coronel'
        abreviatura = 'Cel'
    elif cod_posto_grad == 6:
        descricao = 'Tenente Coronel'
        abreviatura = 'Ten Cel'
    elif cod_posto_grad == 7:
        descricao = 'Major'
        abreviatura = 'Maj'
    elif cod_posto_grad == 8:
        descricao = 'Capitão'
        abreviatura = 'Cap'
    elif cod_posto_grad == 9:
        descricao = 'Primeiro Tenente'
        abreviatura = '1º Ten'
    elif cod_posto_grad == 10:
        descricao = 'Segundo Tenente'
        abreviatura = '2º Ten'
    elif cod_posto_grad == 11:
        descricao = 'Aspirante a Oficial'
        abreviatura = 'Asp'
    elif cod_posto_grad == 12:
        descricao = 'Subtenente'
        abreviatura = 'S Ten'
    elif cod_posto_grad == 13:
        descricao = 'Primeiro Sargento'
        abreviatura = '1º Sgt'
    elif cod_posto_grad == 14:
        descricao = 'Segundo Sargento'
        abreviatura = '2º Sgt'
    elif cod_posto_grad == 15:
        descricao = 'Terceiro Sargento'
        abreviatura = '3º Sgt'
    elif cod_posto_grad == 16:
        descricao = 'Cabo'
        abreviatura = 'Cb'
    elif cod_posto_grad == 17:
        descricao = 'Soldado'
        abreviatura = 'Sd'
    elif cod_posto_grad == 18:
        descricao = 'Taifeiro Mor'
        abreviatura = 'TM'
    elif cod_posto_grad == 19:
        descricao = 'Taifeiro de Primeira Classe'
        abreviatura = 'T1'
    elif cod_posto_grad == 20:
        descricao = 'Taifeiro de Segunda Classe'
        abreviatura = 'T2'
    elif cod_posto_grad == 21:
        descricao = 'Servidor Civil'
        abreviatura = 'SC'
    elif cod_posto_grad == 22:
        descricao = 'Sem Patente'
        abreviatura = 'SP'
    # Inclusao de Cadete e Aluno
    elif cod_posto_grad == 23:
        descricao = 'Cadete'
        abreviatura = 'Cad'
    elif cod_posto_grad == 24:
        descricao = 'Aluno'
        abreviatura = 'Al'
    #    FAB
    elif cod_posto_grad == 101:
        descricao = 'Marechal do Ar'
        abreviatura = 'Mar'
    elif cod_posto_grad == 102:
        descricao = 'Tenente Brigadeiro'
        abreviatura = 'Ten Brig'
    elif cod_posto_grad == 103:
        descricao = 'Major Brigadeiro'
        abreviatura = 'Maj Brig'
    elif cod_posto_grad == 104:
        descricao = 'Brigadeiro'
        abreviatura = 'Brig'
    elif cod_posto_grad == 105:
        descricao = 'Coronel'
        abreviatura = 'Cel'
    elif cod_posto_grad == 106:
        descricao = 'Tenente Coronel'
        abreviatura = 'Ten Cel'
    elif cod_posto_grad == 107:
        descricao = 'Major'
        abreviatura = 'Maj'
    elif cod_posto_grad == 108:
        descricao = 'Capitao'
        abreviatura = 'Cap'
    elif cod_posto_grad == 109:
        descricao = 'Primeiro Tenente'
        abreviatura = '1º Ten'
    elif cod_posto_grad == 110:
        descricao = 'Segundo Tenente'
        abreviatura = '2º Ten'
    elif cod_posto_grad == 111:
        descricao = 'Aspirante a Oficial'
        abreviatura = 'Asp Of'
    elif cod_posto_grad == 112:
        descricao = 'Cadete'
        abreviatura = 'Cad'
    elif cod_posto_grad == 113:
        descricao = 'Sub-Oficial'
        abreviatura = 'SO'
    elif cod_posto_grad == 114:
        descricao = 'Primeiro Sargento'
        abreviatura = '1S'
    elif cod_posto_grad == 115:
        descricao = 'Segundo Sargento'
        abreviatura = '2S'
    elif cod_posto_grad == 116:
        descricao = 'Terceiro Sargento'
        abreviatura = '3S'
    elif cod_posto_grad == 117:
        descricao = 'Aluno'
        abreviatura = 'Al'
    elif cod_posto_grad == 118:
        descricao = 'Cabo'
        abreviatura = 'Cb'
    elif cod_posto_grad == 119:
        descricao = 'Soldado de Primeira Classe'
        abreviatura = 'S1'
    elif cod_posto_grad == 120:
        descricao = 'Soldado de Segunda Classe'
        abreviatura = 'S2'
    elif cod_posto_grad == 121:
        descricao = 'Taifeiro Mor'
        abreviatura = 'TM'
    elif cod_posto_grad == 122:
        descricao = 'Taifeiro de Primeira Classe'
        abreviatura = 'T1'
    elif cod_posto_grad == 123:
        descricao = 'Taifeiro de Segunda Classe'
        abreviatura = 'T2'
    # Marinha
    elif cod_posto_grad == 201:
        descricao = 'Almirante'
        abreviatura = 'Alte'
    elif cod_posto_grad == 202:
        descricao = 'Almirante-de-Esquadra'
        abreviatura = 'Alte Esq'
    elif cod_posto_grad == 203:
        descricao = 'Vice-Almirante'
        abreviatura = 'V Alte'
    elif cod_posto_grad == 204:
        descricao = 'Contra-Almirante'
        abreviatura = 'C Alte'
    elif cod_posto_grad == 205:
        descricao = 'Capitão-de-Mar-e-Guerra'
        abreviatura = 'CMG'
    elif cod_posto_grad == 206:
        descricao = 'Capitão-de-Mar-e-Guerra Intendente'
        abreviatura = 'CMG(IM)'
    elif cod_posto_grad == 207:
        descricao = 'Capitão-de-Fragata'
        abreviatura = 'CF'
    elif cod_posto_grad == 208:
        descricao = 'Capitão-de-Corveta'
        abreviatura = 'CC'
    elif cod_posto_grad == 209:
        descricao = 'Capitão-Tenente'
        abreviatura = 'CT'
    elif cod_posto_grad == 210:
        descricao = 'Primeiro Tenente'
        abreviatura = '1T'
    elif cod_posto_grad == 211:
        descricao = 'Segundo Tenente'
        abreviatura = '2T'
    elif cod_posto_grad == 212:
        descricao = 'Guarda-Marinha'
        abreviatura = 'GM'
    elif cod_posto_grad == 213:
        descricao = 'Aspirante'
        abreviatura = 'Asp'
    elif cod_posto_grad == 214:
        descricao = 'Suboficial'
        abreviatura = 'SO'
    elif cod_posto_grad == 215:
        descricao = 'Primeiro Sargento'
        abreviatura = '1º SG'
    elif cod_posto_grad == 216:
        descricao = 'Segundo Sargento'
        abreviatura = '2º SG'
    elif cod_posto_grad == 217:
        descricao = 'Terceiro Sargento'
        abreviatura = '3º SG'
    elif cod_posto_grad == 218:
        descricao = 'Cabo'
        abreviatura = 'CB'
    elif cod_posto_grad == 219:
        descricao = 'Soldado(CFN)'
        abreviatura = 'SD'
    elif cod_posto_grad == 220:
        descricao = 'Marinheiro'
        abreviatura = 'MN'

    if descricao_e_abreviatura == 2:
        abreviatura = descricao
    elif descricao_e_abreviatura == 3:
        abreviatura += ' - ' + descricao
    return abreviatura

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
