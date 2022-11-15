# -*- coding: utf-8 -*-
import utils, json, re
from urllib.parse import unquote
############################################### Funções de apoio ##########################################
########## Suscetível a IP Spoofing #############
# Caso queira permitir acesso por hosts apenas de uma subrede, edite esta função e use-a como decorator
def check_subnet_ip(callee):
    def wrapper():
        lista_ips_adm = []
        for i in range(2,255):
            lista_ips_adm.append("10.78.4."+str(i))
        if str(request.client) not in lista_ips_adm:
            raise HTTP(404)
        else:
            return callee()
    return wrapper

# /requisicoes/default/getanos?secao=S3
def getanos():
    if request.vars.secao:
        rows=dbpg(dbpg.processo_requisitorio.secao_ano_nr.contains(request.vars.secao)).select(dbpg.processo_requisitorio.secao_ano_nr)
    else:
        rows = []
    #duas secoes com nome parecidos pode dar m aqui
    anos=[r.secao_ano_nr.split("_")[-2] for r in rows]
    anos.append(request.now.strftime('%Y'))
    return response.json(sorted(list(set(anos))))

def getSecoesDesteUser():
    if auth.is_logged_in():
        rows=dbpgsped((dbpgsped.pessoa.nm_login==auth.user.username)&(dbpgsped.pessoa.id_pessoa==dbpgsped.usuario_pessoa.id_pessoa)&(dbpgsped.usuario_pessoa.dt_fim==None) & (dbpgsped.usuario_pessoa.id_usuario==dbpgsped.usuario_secao.id_usuario) & (dbpgsped.secao.id_secao==dbpgsped.usuario_secao.id_secao)).select(dbpgsped.secao.nm_sigla) #nm_sigla
        secoes = [row.nm_sigla for row in rows]
    else:
        secoes = []
    return secoes

def getContasDesteUser():
    if auth.is_logged_in():
        contas=dbpgsped((dbpgsped.pessoa.nm_login==auth.user.username)&(dbpgsped.pessoa.id_pessoa==dbpgsped.usuario_pessoa.id_pessoa)&(dbpgsped.usuario_pessoa.dt_fim==None)&
               (dbpgsped.usuario_pessoa.id_usuario==dbpgsped.usuario.id_usuario)).select(dbpgsped.usuario.id_usuario,dbpgsped.usuario.nm_usuario)
        return [(r.id_usuario,r.nm_usuario) for r in contas]
    else:
        return []

def getComentarios():
    rows=dbpg(dbpg.comentarios.pr.contains(request.vars.processo)).select().as_list()
    retorno = []
    for row in rows:
        retorno.append({"autor":row['autor'],"comentario":row['comentario'],"datahora":row['datahora'].strftime("%d-%m-%Y %H:%M:%S")})
    return response.json(retorno)

def getPrivs():
    is_salc,is_fiscal,is_od,is_admin,is_odsubstituto = False,False,False,False,False
    conf = dbpg(dbpg.configuracoes).select(orderby='id').last()
    if not conf:
        try:
            if int(configuration.get('app.conta_admin')[1]) in [r[0] for r in getContasDesteUser()]:
                is_admin=True
        except:
            pass
        return is_salc,is_fiscal,is_od,is_admin,is_odsubstituto
    for contadesteuser in getContasDesteUser():
        for id_usuario in conf.contas_salc:
            if id_usuario==contadesteuser[0]:
                is_salc=True
        if conf.conta_fiscal==contadesteuser[0]:
            is_fiscal=True
        if conf.conta_od==contadesteuser[0]:
            is_od=True
        if conf.conta_odsubstituto==contadesteuser[0]:
            is_odsubstituto=True
        try:
            if int(list(configuration.get('app.conta_admin'))[1])==contadesteuser[0]:
                is_admin=True
        except:
            pass
    return is_salc,is_fiscal,is_od,is_admin,is_odsubstituto

def getodt():
    def teste_encoding(a):
        if hasattr(a, 'decode'): return a.decode("utf-8")
        else: return a
    processo = unquote(request.vars.processo) if request.vars.processo else ''
    row = dbpg(dbpg.processo_requisitorio.secao_ano_nr==processo).select().first()
    if row:
        try:
            dados = json.loads(row.dados)
        except ValueError:
            # query = dbpg.processo_requisitorio.dados.like('%\\x%')
            # os dados devem ter caracteres unicode no formato \u00VV e não \xVV, editar pelo pgadmin4 causa esse bug!!!
            # Solução é encotrar, copiar os dados, substituir no sublime \x por \u00 e atualizar. Se precisar voltar a valdiade para null:
            #UPDATE public.processo_requisitorio SET valido=null WHERE id=1;-- é o modo correto de editar a validade
            dados = json.loads(row.dados.decode("unicode_escape")) # TODO Aprender como converter em Python 2
            #return response.json({"vars":row.dados,"erro":str(e)+str(e.args)})
    else: raise HTTP(400)
    try:
        from relatorio.templates.opendocument import Template
        from io import open, BytesIO
        meses = [u"Janeiro", u"Fevereiro", u"Março", u"Abril", u"Maio", u"Junho", u"Julho", u"Agosto", u"Setembro" , u"Outubro", u"Novembro", u"Dezembro"]
        mes_abr = [m[:3] for m in meses]
        fbase = open(os.path.join(request.folder,'private','vars.json'),'r', encoding="utf-8").read()
        varsjson = json.loads(fbase)
        varsjson.update(dados)
        dicmodos = {"gerente":"Gerente/Participante", "carona":"Carona","dispensa":u"Dispensa de Licitação","inex":"Inexigibilidade"}
        for quem in ["requisitante","fiscal","od"]:
            for modo in ["gerente", "carona","dispensa","inex","anul"]:
                for doc in ["pr","pedido","comparativo","justificativa","etp"]:
                    if "ass_"+quem+"_"+doc+"_"+modo not in varsjson:
                        varsjson["ass_"+quem+"_"+doc+"_"+modo] = ""
        varsjson['hash']=str(CRYPT(digest_alg="sha256",salt="")(row['dados'])[0])
        try:
            varsjson['secao']=processo.split("_")[0]
            varsjson['ano']=processo.split("_")[1]
            varsjson['nr']=processo.split("_")[2]
        except:
            raise HTTP(400)
        varsjson['dataextenso']= varsjson["data"].split("/")[0] + " de " + meses[int(varsjson["data"].split("/")[1])-1]
        varsjson['dataresumidalower']= teste_encoding(varsjson["data"].split("/")[0]+" "+mes_abr[int(varsjson["data"].split("/")[1])-1])
        varsjson['dataresumidalower']= varsjson['dataresumidalower']
        varsjson['cidadeestado'] = configuration.get('app.orgcidade')+"/"+configuration.get('app.orgestadoabrev')#"Manaus"+"/"+"AM" ##
        varsjson['omextenso'] = configuration.get('app.orgextenso').upper() #"4º CENTRO DE GEOINFORMAÇÃO"#
        varsjson['omabrev'] = configuration.get('app.orgabrev') #"4º CGEO"#
        varsjson['omendereco'] = ", ".join([k for k in configuration.get('app.orgendereco')]) #"Avenida Marechal Bittencourt, nº 97, bairro Santo Antônio, CEP – 69029-160, em Manaus/AM"#
        varsjson['timbre_linha1'] = configuration.get('app.timbre_linha1') #"MINISTÉRIO DA DEFESA"#
        varsjson['timbre_linha2'] = configuration.get('app.timbre_linha2') #"EXÉRCITO BRASILEIRO"#
        varsjson['omsup'] = configuration.get('app.timbre_linha3') #"DCT - DSG"#
        varsjson['objs'] = []
        cp = varsjson.copy()
        for k in cp:
            if "_edited" in k: varsjson.pop(k)
            elif "odsubstituto" in k:
                if varsjson[k]!="":
                    varsjson[k]=varsjson[k]+" "
        qttotaldeitens = []
        for k,v in varsjson.items():
            if "nritem" in k or "catmatitem" in k or "descricaoitem" in k or "qtitens" in k or "valorfornecedor2" in k or "somaparcial" in k :
                qttotaldeitens.append(k.split("-")[1])
        for ordem in sorted(set(qttotaldeitens)):
            varsjson['objs'].append({
                    'nritem':varsjson['nritem-'+ordem].replace("\\n","") if 'nritem-'+ordem in varsjson else "",
                    'descricaoitem':varsjson['descricaoitem-'+ordem] if 'descricaoitem-'+ordem in varsjson else "",
                    'u':varsjson['unidade-'+ordem] if 'unidade-'+ordem in varsjson else "",
                    'unidade':varsjson['unidade-'+ordem] if 'unidade-'+ordem in varsjson else "",
                    'qtitens':varsjson['qtitens-'+ordem] if 'qtitens-'+ordem in varsjson else "",
                    'valor':varsjson['valor-'+ordem] if 'valor-'+ordem in varsjson else "",
                    'catmatitem':varsjson['catmatitem-'+ordem] if 'catmatitem-'+ordem in varsjson else "",
                    'somaparcial':varsjson['somaparcial-'+ordem] if 'somaparcial-'+ordem in varsjson else "",
                    'valorvencedor':varsjson['valorvencedor-'+ordem] if 'valorvencedor-'+ordem in varsjson else "",
                    'valorfornecedor1':varsjson['valorfornecedor1-'+ordem] if 'valorfornecedor1-'+ordem in varsjson else "",
                    'valorfornecedor2':varsjson['valorfornecedor2-'+ordem] if 'valorfornecedor2-'+ordem in varsjson else "",
                    'valorfornecedor3':varsjson['valorfornecedor3-'+ordem] if 'valorfornecedor3-'+ordem in varsjson else "",
                    'valorfornecedor4':varsjson['valorfornecedor4-'+ordem] if 'valorfornecedor4-'+ordem in varsjson else "",
                    'valorcomparacao1':varsjson['valorcomparacao1-'+ordem] if 'valorcomparacao1-'+ordem in varsjson else "",
                    'valorcomparacao2':varsjson['valorcomparacao2-'+ordem] if 'valorcomparacao2-'+ordem in varsjson else "",
                    'valorcomparacao3':varsjson['valorcomparacao3-'+ordem] if 'valorcomparacao3-'+ordem in varsjson else "",
                    'unit2':varsjson['unit2-'+ordem] if 'unit2-'+ordem in varsjson else "",
                    'unit3':varsjson['unit3-'+ordem] if 'unit3-'+ordem in varsjson else ""
                    })
        modelo = "" if varsjson['modo']=="gerente" else "_dispensa" if varsjson['modo']=="dispensa" else "_anul" if varsjson['modo']=="anul" else "_carona"
        varsjson['aquisicaopor'] = dicmodos.get(varsjson['modo'],"Gerente") if varsjson['modo']!="gerente" else u"Pregão "+varsjson['gerpar']
        ## SolUÇÃO para: "'ascii' codec can't decode byte 0xc3 in position 9: ordinal not in range(128)"
        # varsjson["key"] = teste_encoding(varsjson["key"])
        filename2=os.path.join(request.folder,'static','modelos','pr'+modelo+'_model.odt')
        basic = Template(source='', filepath=filename2)
        bufferimg = BytesIO()
        bufferimg.write(basic.generate(o=varsjson).render().getvalue())
        bufferimg.seek(0)
        return response.stream(bufferimg,filename="PR_"+processo+".odt",attachment=True)
    except Exception as e:
        return response.json({"vars":varsjson,"erro":str(e)+str(e.args)})
############################################### Fim funções de apoio ##########################################
#@check_subnet_ip
def index():
    retorno = ""
    if request.vars.secao_change:
        redirect(URL('default', 'index', vars=dict(secao=request.vars.sec,ano=request.vars.ano,nr="01")))
    if not request.vars.secao:
        secao = configuration.get('app.secao_escape')
    else:
        secao = request.vars.secao
    nr = request.vars.nr if request.vars.nr else "01"
    ano = request.vars.ano if request.vars.ano else request.now.strftime('%Y')
    if not request.vars.secao or not request.vars.ano or not request.vars.nr:
        redirect(URL('default', 'index', vars=dict(secao=secao,ano=ano,nr=nr)))
    # Validação das seções
    SECOES = get_secoes()
    if SECOES and secao not in SECOES:
        redirect(URL('default', 'index', vars=dict(secao=SECOES[-1],ano=ano,nr=nr)))
    # Validação da secao que está sendo editada
    secoesdesteuser = getSecoesDesteUser()
    editavel = True if secao in secoesdesteuser else False
    # Validação dos niveis de autorização para este user
    is_salc,is_fiscal,is_od,is_admin,is_odsubstituto = getPrivs()
    rows = dbpg(dbpg.processo_requisitorio.secao_ano_nr.contains(secao+"_"+ano)).select(orderby=~dbpg.processo_requisitorio.id)
    nr="01" if not rows else nr
    if not rows:# nenhum lançamento ainda
        hashed = ""
        row = {"dados":""}
        arq_carona = []
        arq_dispensa = []
        arq_inex = []
        validade = None
    else:
        row = dbpg(dbpg.processo_requisitorio.secao_ano_nr.contains(secao+"_"+ano+"_"+nr)).select().first().as_dict()
        hashed = str(CRYPT(digest_alg="sha256",salt="")(row['dados'])[0])
        # pegar as url dos arquivos
        arq_carona = dbpg((dbpg.anexos.pr==secao+"_"+ano+"_"+nr)&(dbpg.anexos.modo=="carona")).select().as_list()
        arq_dispensa = dbpg((dbpg.anexos.pr==secao+"_"+ano+"_"+nr)&(dbpg.anexos.modo=="dispensa")).select().as_list()
        arq_inex = dbpg((dbpg.anexos.pr==secao+"_"+ano+"_"+nr)&(dbpg.anexos.modo=="inex")).select().as_list()
        validade = row['valido']
    return dict(mk_popoverhtml=utils.mk_popoverhtml,ano=ano,nr=nr,secao=secao,form_user=auth.login(next=URL(args=request.args, vars=request.get_vars, host=True)),
                retorno=retorno,rows=rows,row=row,SECOES=SECOES,arq_carona=arq_carona,arq_dispensa=arq_dispensa,arq_inex=arq_inex,validade=json.dumps(validade),
                editavel=editavel,is_salc =is_salc, is_fiscal = is_fiscal, is_od = is_od, is_admin = is_admin, hashed=hashed
               )

def pedencias():
    msg = ""
    quem = request.args[0] if len(request.args) else "od"
    response.view = 'default/pesquisar.html'
    is_salc,is_fiscal,is_od,is_admin,is_odsubstituto = getPrivs()
    q = request.vars.q if request.vars.q else redirect(URL('default', 'pedencias', args=[quem],vars=dict(q=request.now.strftime('%Y'))))
    if quem in ["fiscal", "od"]:
        rows = dbpg((dbpg.processo_requisitorio.valido==True) & (dbpg.processo_requisitorio.secao_ano_nr.contains(q)) ).select(orderby='id')
    elif quem in ["requisitante","salc"]:
        rows = dbpg((dbpg.processo_requisitorio.valido==None) & (dbpg.processo_requisitorio.secao_ano_nr.contains(q)) ).select(orderby='id')
    else:
        rows = []
    # Checagem das assinaturas dessas rows
    rows2 = []
    lista_assinaturas = []
    for row in rows:
        try:
            dic = json.loads(row.dados)
        except Exception as e:
            s = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', row.dados)
            dic = json.loads(s)
            msg = str(e)+"---- Processo: ("+str(row.id)+") "+str(row.secao_ano_nr)
        modo = dic.get('modo','gerente')
        if quem=="salc": w="requisitante"
        else: w=quem
        if modo == "anul":
            lista_assinaturas = ["ass_"+w+"_pr_"+modo]
        elif modo == "inex":
            lista_assinaturas = ["ass_"+w+"_pr_"+modo,"ass_"+w+"_pedido_"+modo,"ass_"+w+"_justificativa_"+modo,"ass_"+w+"_etp_"+modo]
        elif modo == "dispensa":
            lista_assinaturas = ["ass_"+w+"_pr_"+modo,"ass_"+w+"_pedido_"+modo,"ass_"+w+"_justificativa_"+modo]
        elif modo == "carona":
            lista_assinaturas = ["ass_"+w+"_pr_"+modo,"ass_"+w+"_pedido_"+modo,"ass_"+w+"_justificativa_"+modo, "ass_"+w+"_etp_"+modo]
        elif modo == "gerente":
            lista_assinaturas = ["ass_"+w+"_pr_gerente","ass_"+w+"_pedido_gerente"]
        if quem in ["requisitante","salc"] and modo not in[ "gerente","dispensa"]:
            lista_assinaturas.append("ass_"+w+"_comparativo_"+modo)
        if quem=="salc":
            if all(l in dic for l in lista_assinaturas):
                rows2.append(row.as_dict())
        else:
            for l in lista_assinaturas:
                if l not in dic:
                    rows2.append(row.as_dict())
                    break
    return dict(rows=rows2,form_user=auth.login(next=URL(args=request.args, vars=request.get_vars, host=True)), is_salc=is_salc, is_admin=is_admin, 
                is_od=is_od, is_fiscal=is_fiscal, q="Pendências do(a) "+quem.upper(), msg=msg)

def pesquisar():
    msg = ""
    is_salc,is_fiscal,is_od,is_admin,is_odsubstituto = getPrivs()
    rows =[]
    if request.vars.q:
        q = request.vars.q
        rows.extend(dbpg((dbpg.processo_requisitorio.secao_ano_nr.contains(q)) | (dbpg.processo_requisitorio.resumo.contains(q)) | (dbpg.processo_requisitorio.dados.contains(q))).select().as_list())
    else:
        q=""
    return dict(rows=rows,form_user=auth.login(next=URL(args=request.args, vars=request.get_vars, host=True)),is_salc=is_salc,is_admin=is_admin,is_od=is_od,is_fiscal=is_fiscal,q=q,msg=msg)

@auth.requires_login()
def profile():
    contasdesteuser = getContasDesteUser()
    is_salc,is_fiscal,is_od,is_admin,is_odsubstituto = getPrivs()
    salc,fiscal,od,admin,odsubstituto = ["Sim" if f else "Não" for f in [is_salc,is_fiscal,is_od,is_admin,is_odsubstituto]]
    logado = auth.user.as_dict()
    pessoa = dbpgsped(dbpgsped.pessoa.nm_login==auth.user.username).select().first().as_dict()
    pessoa['patente'] = utils.posto_graduacao(pessoa['cd_patente'], 1)
    usuarios = {}
    for usuario in dbpgsped( (dbpgsped.usuario_pessoa.id_pessoa==pessoa['id_pessoa']) & (dbpgsped.usuario_pessoa.dt_fim==None)).select(dbpgsped.usuario_pessoa.id_usuario):
        usuarios[usuario.id_usuario]=dbpgsped.usuario(usuario.id_usuario).as_dict()
    del pessoa['id']
    del pessoa['id_pessoa']
    del pessoa['cd_patente']
    contas = {}
    for usuario in usuarios:
        s = dbpgsped(dbpgsped.usuario_secao.id_usuario==usuarios[usuario]['id_usuario']).select().first().id_secao
        sr = dbpgsped.secao(s).as_dict()
        contas[usuarios[usuario]['nm_usuario']] = "Seção: "+sr['nm_sigla']
    return dict(perfil={'Contas':contas, 'Pessoa':pessoa, 'Privilégios':{"Admin":admin,"OD":od,"Fiscal":fiscal,"Salc":salc,"OD Substituto":odsubstituto}},
                is_salc=is_salc,is_admin=is_admin,is_od=is_od,is_fiscal=is_fiscal)

@auth.requires_login()
def conf():
    contasdesteuser = getContasDesteUser()
    record = dbpg(dbpg.configuracoes).select(orderby='id')
    is_salc,is_admin = False,False
    for contadesteuser in contasdesteuser:
        if record:
            for id_usuario in record.last().contas_salc:
                if id_usuario==contadesteuser[0]:
                    is_salc=True
        try:
            if int(configuration.get('app.conta_admin')[1])==contadesteuser[0]:
                is_admin=True
        except:
            pass
    if not (is_admin or is_salc): raise HTTP(403)
    dbpg.configuracoes.id.readable = False
    dbpg.configuracoes.contas_salc.requires = IS_IN_DB(dbpgsped(dbpgsped.usuario.in_excluido != "s"), 'usuario.id','%(nm_usuario)s: %(id_usuario)s',multiple=True)
    dbpg.configuracoes.conta_fiscal.requires = IS_IN_DB(dbpgsped(dbpgsped.usuario.in_excluido != "s"), 'usuario.id','%(nm_usuario)s: %(id_usuario)s')
    dbpg.configuracoes.conta_od.requires = IS_IN_DB(dbpgsped(dbpgsped.usuario.in_excluido != "s"), 'usuario.id','%(nm_usuario)s: %(id_usuario)s')
    dbpg.configuracoes.conta_odsubstituto.requires = IS_IN_DB(dbpgsped(dbpgsped.usuario.in_excluido != "s"), 'usuario.id','%(nm_usuario)s: %(id_usuario)s')
    form=SQLFORM(dbpg.configuracoes,record.last(),submit_button='Enviar',formstyle='bootstrap4_stacked') if record else SQLFORM(dbpg.configuracoes,submit_button='Enviar')
    if form.process().accepted:
        response.flash = 'Edições salvas!'
        #redirect(URL('conf'))
    elif form.errors:
        response.flash = 'Formulário tem erros!'
    else:
        response.flash = 'Por Favor, preencha o formulário!'
    return dict(form=form,is_admin=is_admin,is_salc=is_salc)

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    if "profile" in request.args:
        redirect(URL('profile'))
    if "logout" in request.args:
        if "ano" in request.vars and "nr" in request.vars and "secao" in request.vars:
            auth.logout(next=URL('index',vars=dict(ano=request.vars.ano,nr=request.vars.nr,secao=request.vars.secao)))
        else:
            auth.logout()
    return dict(form_user=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

# ---- action to server uploaded static content (required) ---
@cache.action()
def download2():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download2/[filename]
    """
    return response.download(request, dbpg)

# https://127.0.0.1/requisicoes/default/api?novo=0
@request.restful()
def api():
    if not auth.is_logged_in(): # somente usuários logados podem usar esta API
        raise HTTP(401)
    def secoes_deste_user():
        rows=dbpgsped((dbpgsped.pessoa.nm_login==auth.user.username)&(dbpgsped.pessoa.id_pessoa==dbpgsped.usuario_pessoa.id_pessoa)&(dbpgsped.usuario_pessoa.dt_fim==None) & (dbpgsped.usuario_pessoa.id_usuario==dbpgsped.usuario_secao.id_usuario) & (dbpgsped.secao.id_secao==dbpgsped.usuario_secao.id_secao)).select(dbpgsped.secao.nm_sigla) #nm_sigla
        return [row.nm_sigla for row in rows]
    def contas_do_user(user): # reinterpretação de usuarios_da_pessoa(pessoa)
        #contas=dbpgsped((dbpgsped.pessoa.nm_login==auth.user.username)&(dbpgsped.pessoa.id_pessoa==dbpgsped.usuario_pessoa.id_pessoa)&(dbpgsped.usuario_pessoa.dt_fim==None)&
        #       (dbpgsped.usuario_pessoa.id_usuario==dbpgsped.usuario.id_usuario)).select(dbpgsped.usuario.id_usuario,dbpgsped.usuario.nm_usuario)
        contas=dbpgsped((dbpgsped.pessoa.nm_login==user)&(dbpgsped.pessoa.id_pessoa==dbpgsped.usuario_pessoa.id_pessoa)&(dbpgsped.usuario_pessoa.dt_fim==None)&
               (dbpgsped.usuario_pessoa.id_usuario==dbpgsped.usuario.id_usuario)).select(dbpgsped.usuario.id_usuario,dbpgsped.usuario.nm_usuario)
        return [(r.id_usuario,r.nm_usuario) for r in contas]
    def anos_com_processos_desta_secao(secao):
        rows=dbpg(dbpg.processo_requisitorio.secao_ano_nr.contains(secao)).select(dbpg.processo_requisitorio.secao_ano_nr) #duas secoes com nome parecidos pode dar m aqui
        # "_".join(a.split("_")[:-2]) -> para sempre pegar o nome da secao independe se houver "_" dentro do nome
        anos=[r.secao_ano_nr.split("_")[-2] for r in rows]
        return sorted(list(set(anos)))
    def GET(*args, **vars):
        dic=dict(anos=False,secoesdesteuser=False)
        dic['vars'] = vars
        for key, value in dic.items():
            if key in vars: dic.update({key:True if (vars[key] == "1" or vars[key] == "true") else False})
        if dic['anos']:
            try:
                dic['vars'] = vars
                secao = vars.pop('secao')
                dic['anos'] = anos_com_processos_desta_secao(secao)
            except Exception as e:
                raise HTTP(400,H2(e))
        if dic['secoesdesteuser']:
            try:
                dic['vars'] = vars
                dic['secoes'] = list(set(secoes_deste_user()))
            except Exception as e:
                raise HTTP(400,H2(e))
        return response.json(dic)
    def POST(*args, **vars):
        dic=dict(novo=False,edit=False,assinar=False,comentar=False,remline=False)
        for key, value in dic.items():
            if key in vars: dic.update({key:True if (vars[key] == "1" or vars[key] == "true") else False})
        #clean data
        vars['processo'] = unquote(vars.get('processo',""))
        allowed = list(ALLOWED)
        if dic['novo']:
            try:
                resumo = vars.pop('resumo')
                ano = vars.pop('ano')
                secao = vars.pop('secao')
                groups = secoes_deste_user()
                dic['grupos_deste_user'] = groups
            except Exception as e:
                raise HTTP(400,H2(e))
            try:
                if secao not in groups:
                    raise HTTP(403)
                else:
                    last = dbpg(dbpg.processo_requisitorio.secao_ano_nr.like(secao+'_'+ano+'%')).select(orderby='id').last()
                    nr = "%02d"%(int(last.secao_ano_nr.split("_")[-1])+1) if last else "01"
                    dbpg.processo_requisitorio.insert( secao_ano_nr=secao+'_'+ano+'_'+nr, resumo=resumo ,dados=response.json({"data":request.now.strftime('%d/%m/%Y'),"modo":"gerente"}))
                    dic['nr']=nr
                    dic['redirect2']=URL('default', 'index',vars=dict(secao=secao,ano=ano,nr=nr))
            except Exception as e:
                raise HTTP(403,H2(e))
        if dic['edit']:
            try:
                if vars['processo'].split("_")[0] not in secoes_deste_user(): raise HTTP(403,H2("Usuário não pertence a esta seção."))
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                if pr['valido']!=None: raise HTTP(400,H2("Este processo já foi encerrado."))
                #1) Proteção contra caracteres mal escapados
                try:
                    dados = json.loads(pr['dados'])
                except Exception as e:
                    s = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', pr['dados'])
                    dados = json.loads(s)
                esta_url=URL('default', 'index',vars=dict(secao=vars['processo'].split("_")[0],ano=vars['processo'].split("_")[-2],nr=vars['processo'].split("_")[-1]))
                #2) Acabar com todas as assinaturas
                campos_assinados = [ k for k,v in dados.items() if "ass_" in k]
                for c in campos_assinados:
                    dados.pop(c)
                #3) Adicionar modo
                lista_modos = ["gerente","carona","dispensa","inex","anul"]
                if vars['modo'] in lista_modos and 'modo' not in dados: dados['modo'],dic['redirect2']=vars['modo'],esta_url
                elif vars['modo'] in lista_modos and 'modo' in dados and dados['modo']!=vars['modo']: dados['modo'],dic['redirect2']=vars['modo'],esta_url
                elif vars['modo'] in lista_modos and 'modo' in dados and dados['modo']==vars['modo']: dados['modo']=vars['modo']
                else: dados['modo'],dic['redirect2']="gerente",esta_url
                #4) Edição propriamente dita
                dados[vars['campo']]=re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})' , r'', vars['valor'].replace('"',"'").replace('\n',"\\n"))
                dados[vars['campo']+'_edited']='true'
                pr['dados']=json.dumps(dados, sort_keys=True )
                pr.update_record()
                if campos_assinados:
                    dic['redirect2']=esta_url
                dic['hashed']=str(CRYPT(digest_alg="sha256",salt="")(pr['dados'])[0])
            except Exception as e:
                raise HTTP(400,CAT(H2(e),P(str(pr['dados']))))
        if dic['assinar']:
            if 'senha' in vars and 'login' in vars:
                import ldap
                ldap_host = configuration.get('sped.host') if configuration.get('sped.host') else configuration.get('ldap.host')
                l = ldap.initialize('ldap://'+ldap_host)
                username = "cn=%s,%s" % (vars['login'],BASE_DN)
                password = vars['senha']
                try:
                    l.protocol_version = ldap.VERSION3
                    l.simple_bind_s(username, password)
                except Exception as error:
                    raise HTTP(401)
            else:
                raise HTTP(400)
            # Pegar Post Nome Completo desse login no banco do sped
            try:
                import random,string
            except:
                raise HTTP(500)
            try:
                pessoa = dbpgsped(dbpgsped.pessoa.nm_login==vars['login']).select().first().as_dict()
                pessoa['patente'] = utils.posto_graduacao(pessoa['cd_patente'], 1)
                #pessoa['patente'] = dbpgsped.executesql("SELECT posto_graduacao(%d,1);"%pessoa['cd_patente'])[0][0]
                militar = pessoa['patente'] + " " + pessoa['nm_guerra']+ " - "+ pessoa['nm_completo']
            except:
                raise HTTP(500)
            dic['militar']=militar
            # Pegar as contas dessa pessoa
            try:
                contas = contas_do_user(vars['login'])
                dic['contas']=contas
            except:
                raise HTTP(500)
            # Comparar o cmapo da assinatura com as autorizações da pessoa que está assinando
            conf = dbpg(dbpg.configuracoes).select(orderby='id').last()
            is_salc = False
            is_fiscal = False
            is_od = False
            is_odsubstituto = False
            odsubstituto = ""
            autorizado = False
            for contadesteuser in contas:
                if conf:
                    for id_usuario in conf.contas_salc:
                        if dbpgsped.usuario(id_usuario).nm_usuario==contadesteuser[1]:
                            is_salc=True
                    if conf.conta_fiscal and dbpgsped.usuario(conf.conta_fiscal).nm_usuario==contadesteuser[1]:
                        is_fiscal=True
                    if conf.conta_od and dbpgsped.usuario(conf.conta_od).nm_usuario==contadesteuser[1]:
                        is_od=True
                    if conf.conta_odsubstituto and dbpgsped.usuario(conf.conta_odsubstituto).nm_usuario==contadesteuser[1]:
                        is_odsubstituto=True
            if "_requisitante" in vars['campo']: autorizado = True
            elif "_fiscal" in vars['campo'] and is_fiscal: autorizado = True
            elif "_od" in vars['campo'] and is_od: autorizado = True
            elif "_od" in vars['campo'] and is_odsubstituto:
                autorizado = True
                odsubstituto = "Substituto"
                dic['substituto']=vars['campo'].replace("ass_od","odsubstituto")
            else: raise HTTP(401)
            dic['is_salc']=is_salc
            dic['is_fiscal']=is_fiscal
            dic['is_od']=is_od
            dic['is_odsubstituto']=is_odsubstituto
            # Pegar o conjunto de dados deste documento
            try:
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                dados = json.loads(pr['dados'])
            except:
                # Não encontrou?
                raise HTTP(400)
            # gerar uma código de assinatura
            lettersAndDigits = string.ascii_uppercase + string.digits
            flag = 1
            while flag>0 and flag<=10:
                try:
                    codigo = ''.join(random.choice(lettersAndDigits) for i in range(6))
                    dbpg.assinaturas.insert(cod=codigo,militar=militar,pr=vars['processo'],documento_assinado=vars['campo'])
                    flag=0
                except Exception as e:
                    # chegar aqui significa "unique key constrait violation" no campo código
                    # Deve-se repetir essa iteração
                    flag = 1
            if flag>0:
                raise HTTP(500)
            dic['codigo']=codigo
            assinatura = militar + " - " + codigo + " - " + request.now.strftime("%d-%m-%Y %H:%M:%S")
            # Atualizar o conjunto de dados deste documento
            dados[vars['campo']]=assinatura
            dados[vars['campo']+'_edited']='true'
            if "_od" in vars['campo']: dados[vars['campo'].replace("ass_od","odsubstituto")]=odsubstituto
            pr['dados']=json.dumps(dados, sort_keys=True)
            pr.update_record()
            dic['assinatura']=assinatura
            dic['hashed']=str(CRYPT(digest_alg="sha256",salt="")(pr['dados'])[0])
        if dic['comentar']:
            try:
                pessoa = dbpgsped(dbpgsped.pessoa.nm_login==auth.user.username).select().first().as_dict()
                pessoa['patente'] =  utils.posto_graduacao(pessoa['cd_patente'], 1)
                #pessoa['patente'] =  dbpgsped.executesql("SELECT posto_graduacao(%d,1);"%pessoa['cd_patente'])[0][0]
                autor = pessoa['patente'] + " " + pessoa['nm_guerra']+ " - "+ pessoa['nm_completo']
                dic['autor']=autor
                dic['datahora']=request.now.strftime("%d-%m-%Y %H:%M:%S")
                dic['comentario']=vars.pop('comentario')
                dbpg.comentarios.insert(pr=vars.pop('processo'),
                                        autor=autor,
                                        comentario=dic['comentario'])
            except Exception as e:
                raise HTTP(400,H2(e))
        if dic['remline']:
            """
            """
            if vars['processo'].split("_")[0] not in secoes_deste_user():
                raise HTTP(403,H2("Usuário não pertence a esta seção."))
            try:
                ordem=int(vars.pop('ord'))
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                dados = json.loads(pr['dados'])
            except:
                # Não encontrou?
                raise HTTP(400)
            if pr['valido']!=None: raise HTTP(400,H2("Este processo já foi encerrado."))
            dic['vars']=[]
            countlinhas_pedido=[]
            variaveis_tipo_lista = ['nritem','descricaoitem','unidade','qtitens','valor','somaparcial','valorvencedor','valorcomparacao1',
                                    'valorcomparacao2','valorcomparacao3','unit2','unit3']
            variaveis_parecidas_com_lista = ['ncvalor']
            dados_copy = dados.copy()
            for k, v in dados_copy.items():
                if "-"+str(ordem) in k:
                    dic['vars'].append({k:dados.pop(k)})
                for val in variaveis_tipo_lista:
                    if val in k and "_edited" not in k and k not in variaveis_parecidas_com_lista:
                        # BUG: tinha um erro de listindex out of range aqui
                        # CORRIGIDO: adição de variaveis_parecidas_com_lista
                        try:
                            countlinhas_pedido.append(int(k.split("-")[1]))
                        except:
                            raise HTTP(500,H2(k))
                        break
            if countlinhas_pedido:
                countlinhas_pedido = max(countlinhas_pedido)
            else:
                countlinhas_pedido = 1
            dic['qtlinhas']=countlinhas_pedido
            while countlinhas_pedido>=ordem:
                ordem+=1
                for k, v in dados.items():
                    if "-"+str(ordem) in k:
                        dados[k.replace("-"+str(ordem),"-"+str(ordem-1))]=dados.pop(k)
                        countlinhas_pedido+=1
            pr['dados']=json.dumps(dados)
            pr.update_record()
        if "up" in args:
            if vars['processo'].split("_")[0] not in secoes_deste_user():
                return response.json({"error":"Usuário não pertence a esta seção."})
            if "carona" in args: modo = "carona"
            elif "dispensa" in args: modo = "dispensa"
            elif "inex" in args: modo = "inex"
            else: response.json({"error":"Modo não permitido"})
            from io import BytesIO
            try:
                anexos_deste_processo = dbpg(dbpg.anexos.pr==vars['processo']).select()
                total = 0
                for a in anexos_deste_processo:
                    try:
                        total+=int(a.tamanho)
                    except:
                        pass
                filesize = len(vars['file-data'].value)
                total+=filesize
                if total>MAXSIZE*1024: return response.json({"error":"Tamanho total dos arquivos (%s KB) maior que o limite máximo (%s KB)."%(str(total/1024),str(MAXSIZE))})
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                if pr['valido']!=None: return response.json({"error":"Este processo já foi encerrado."})
                dados = json.loads(pr['dados'])
                dados['modo']=modo
                filename = vars['file-data'].filename
                if filename.split(".")[-1] in allowed:
                    nid = dbpg.anexos.insert(arquivo=dbpg.anexos.arquivo.store(BytesIO(vars['file-data'].value), filename),
                                   modo=modo,
                                   tamanho=str(filesize),
                                   name=filename,
                                   pr=vars['processo'])
                    pr['dados']=json.dumps(dados)
                    pr.update_record()
                    return response.json({
                            'initialPreviewAsData' : True,
                            'initialPreview' : URL(request.application,'download2', dbpg.anexos(nid)['arquivo']),
                            "initialPreviewConfig": [
                                {
                                    'key' : nid,
                                    'caption' : filename,
                                    'size' : filesize,
                                    'downloadUrl' : URL(request.application,'download2', dbpg.anexos(nid)['arquivo']),
                                    'url' : URL("api","del",vars=dict(processo=vars['processo'])),

                                }
                            ]
                        })
                else:
                    return response.json({"error":"Extensão não permitida"})
            except Exception as e:
                raise HTTP(500,H2(str(e)+str(filename.split(".")[-1] in allowed)))
        if "del" in args:
            try:
                if vars['processo'].split("_")[0] not in secoes_deste_user():
                    return response.json({"error":"Usuário não pertence a esta seção."})
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                if pr['valido']!=None:
                    return response.json({"error":"Este processo já foi encerrado."})
                anexo_row = dbpg.anexos(int(vars['key']))
                if not anexo_row:
                    return response.json({"error":"Arquivo não encontrado!"})
                pr2 = anexo_row['pr']
                if pr2.split("_")[0] not in secoes_deste_user():
                    return response.json({"error":"Usuário não pertence a esta seção!"})
                if pr2!=vars['processo']:
                    return response.json({"error":"Arquivo não pertence a este processo!"})
                dbpg(dbpg.anexos.id==int(vars['key'])).delete()
            except Exception as e:
                raise HTTP(500,H2(str(e)))
        return response.json(dic)
    def PUT(*args, **vars):
        dic=dict(validar=False,invalidar=False,clonar=False)
        for key, value in dic.items():
            if key in vars: dic.update({key:True if (vars[key] == "1" or vars[key] == "true") else False})
        if dic['validar']:
            # Pegar o conjunto de dados deste documento
            try:
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
            except:
                # Não encontrou?
                raise HTTP(400)
            if pr['valido']!=None: raise HTTP(400,H2("Este processo já foi encerrado."))
            pr['valido']=True
            dic['redirect2']=URL('default', 'index',vars=dict(secao=vars['processo'].split("_")[0],ano=vars['processo'].split("_")[-2],nr=vars['processo'].split("_")[-1]))
            pr.update_record()
        if dic['invalidar']:
            # Pegar o conjunto de dados deste documento
            try:
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
            except:
                # Não encontrou?
                raise HTTP(400)
            if pr['valido']!=None: raise HTTP(400,H2("Este processo já foi encerrado."))
            pr['valido']=False
            dic['redirect2']=URL('default', 'index',vars=dict(secao=vars['processo'].split("_")[0],ano=vars['processo'].split("_")[-2],nr=vars['processo'].split("_")[-1]))
            pr.update_record()
        if dic['clonar']:
            # Pegar o conjunto de dados deste documento
            try:
                pr = dbpg(dbpg.processo_requisitorio.secao_ano_nr==vars['processo']).select().first()
                dados = json.loads(pr['dados'])
                secao=vars['secao']
                ano=vars['ano'] if 'ano' in vars else request.now.strftime('%Y') # Brecha proposital
                resumo=vars['resumo']
                groups = secoes_deste_user()
            except: # Não encontrou?
                raise HTTP(400)
            # Checar novamente se ele tem permissão para inserir nesta seção
            if secao not in groups:
                raise HTTP(403)
            # montagem dos dados a serem inseridos
            try:
                last = dbpg(dbpg.processo_requisitorio.secao_ano_nr.like(secao+'_'+ano+'%')).select(orderby='id').last()
                nr = "%02d"%(int(last.secao_ano_nr.split("_")[-1])+1) if last else "01"
                dados["data"]=request.now.strftime('%d/%m/%Y')
                #1) Acabar com todas as assinaturas
                campos_assinados = [ k for k,v in dados.items() if "ass_" in k]
                for c in campos_assinados:
                    dados.pop(c)
            except: # qq bug é bad request, foda-se
                raise HTTP(500)
            # Inserção
            dbpg.processo_requisitorio.insert(secao_ano_nr=secao+'_'+ano+'_'+nr,
                                              resumo=resumo,
                                              dados=response.json(dados))
            dic['nr']=nr
            dic['redirect2']=URL('default', 'index',vars=dict(secao=secao,ano=ano,nr=nr))
            #dbpg.processo_requisitorio.insert()
        dic['vars'] = vars
        return response.json(dic)
    def DELETE(*args, **vars):
        return dict()
    return locals()
