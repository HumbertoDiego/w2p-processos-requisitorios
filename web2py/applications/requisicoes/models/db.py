# -*- coding: utf-8 -*-
from gluon.contrib.appconfig import AppConfig
from gluon.tools import Auth
import os,json

if request.global_settings.web2py_version < "2.15.5":
    raise HTTP(500, "Requires web2py 2.15.5 or newer")

request.requires_https()

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
configuration = AppConfig(reload=True)

db = DAL(configuration.get('db.uri'),
         pool_size=configuration.get('db.pool_size'),
         migrate_enabled=configuration.get('db.migrate'),
         check_reserved=['all'])
OMENDERECO = ", ".join(configuration.get('app.orgendereco'))
BASE_DN    = ",".join(configuration.get('sped.base_dn'))
ALLOWED    = configuration.get('app.allowed_ext')
MAXSIZE    = int(configuration.get('app.maxtotalfsize'))
try:
    CHANGELOG = json.loads(open(os.path.join(request.folder, 'private', 'changelog.json')).read())
except Exception as e:
    CHANGELOG = {"latest":str(e)}
try:
    VARS = json.loads(open(os.path.join(request.folder, 'private', 'vars.json')).read())
except Exception as e:
    VARS = {"erro":str(e)}
LDAP_URI = "postgres2:psycopg2://"+os.environ.get("POST_USER","postgres")+":"+os.environ.get("POST_PASSWORD","secret")+"@"+os.environ.get("POST_HOST","post")+":5432/"
DBPG_URI = LDAP_URI + os.environ.get("POST_APPDB","requisicoes")
LDAP_URI += os.environ.get("POST_AUTHDB","authdb")
# postgres2:psycopg2://postgres:secret@post:5432/requisicoes

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = [] 
if request.is_local and not configuration.get('app.production'):
    response.generic_patterns.append('*')

# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = 'bootstrap4_inline'
response.form_label_separator = ''

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=configuration.get('host.names'))

# -------------------------------------------------------------------------
# create all tables needed by auth, maybe add a list of extra fields
# -------------------------------------------------------------------------
auth.settings.extra_fields['auth_user'] = []
auth.settings.actions_disabled=['register','change_password','request_reset_password','retrieve_username','profile']
auth.settings.remember_me_form=False
auth.define_tables(username=True, signature=False)
auth.settings.create_user_groups = None

# -------------------------------------------------------------------------
# Login pelo SPED
# -------------------------------------------------------------------------
from gluon.contrib.login_methods.ldap_auth import ldap_auth
auth.settings.login_methods.append(
        ldap_auth(db=db,
                  mode='cn',
                  server=configuration.get('sped.host') if configuration.get('sped.host') else configuration.get('ldap.host'),
                  base_dn=BASE_DN,
                  manage_user=True,
                  user_firstname_attrib='givenName',
                  user_lastname_attrib='sn',
                  user_mail_attrib='displayName'
                  )
)
# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------
# read more at http://dev.w3.org/html5/markup/meta.name.html
# -------------------------------------------------------------------------
response.meta.author = configuration.get('app.author')
response.meta.description = configuration.get('app.description')
response.meta.keywords = configuration.get('app.keywords')
response.meta.generator = configuration.get('app.generator')

if configuration.get('sped.uri'):
    try:
        dbpgsped = DAL(configuration.get('sped.uri'),
                    pool_size=configuration.get('sped.pool_size'),
                    migrate_enabled=False,
                    check_reserved=['all'])
    except:
        def get_secoes():
            return []
        dbpgsped = None
else:
    try:
        dbpgsped = DAL(LDAP_URI,
                    pool_size=configuration.get('ldap.pool_size'),
                    migrate_enabled=True,
                    check_reserved=['all'])
    except:
        dbpgsped = DAL(LDAP_URI,
                    pool_size=configuration.get('ldap.pool_size'),
                    migrate_enabled=False,
                    check_reserved=['all'])
if dbpgsped:
    def get_secoes():
        tempo = 60*60*5
        SECOES = [s['nm_sigla'] for s in dbpgsped((dbpgsped.secao.id_pai!=0)&(dbpgsped.secao.in_excluido!="s")).select(dbpgsped.secao.nm_sigla, orderby=dbpgsped.secao.nm_sigla)]
        # Adicionar as seções que mudaram de nome (s3 -> S3) e que possuem algum processo armazenado
        SECOES_PROCESSOS = [s['secao_ano_nr'].split("_")[0] for s in dbpg().select(dbpg.processo_requisitorio.secao_ano_nr)]
        S = sorted(list(set(SECOES+SECOES_PROCESSOS)))
        t = cache.ram('secoes', lambda: S, time_expire=tempo)
        return S

#Change to False if psycopg2.errors.DuplicateTable: relation "usuario" already exists
migrate_bool = True

dbpgsped.define_table('usuario',
                    Field('id_usuario','id'),
                    Field('nm_usuario'),
                    Field('in_excluido'),
                    format='%(id_usuario)s - %(nm_usuario)s',
                    migrate=migrate_bool
                )

dbpgsped.define_table('pessoa',
                    Field('id_pessoa','id'),
                    Field('nm_login'),
                    Field('nm_completo'),
                    Field('cd_patente','integer'),
                    Field('nm_guerra'),
                    format='%(id_pessoa)s - %(nm_guerra)s - %(nm_completo)s',
                    migrate=migrate_bool
                    )
dbpgsped.define_table('secao',
                    Field('id_secao','id'),
                    Field('id_pai','integer'),
                    Field('nm_sigla'),
                    Field('in_excluido'),
                    format='%(id_secao)s - %(nm_sigla)s',
                    migrate=migrate_bool
                    )
dbpgsped.define_table('usuario_pessoa',
                    Field('id_usuario_pessoa','id'),
                    Field('id_usuario',dbpgsped.usuario),
                    Field('id_pessoa',dbpgsped.pessoa),
                    Field('dt_fim'),
                    migrate=migrate_bool
                    )
dbpgsped.define_table('usuario_secao',
                    Field('id_usuario',dbpgsped.usuario),
                    Field('id_secao',dbpgsped.secao),
                    primarykey=['id_usuario', 'id_secao'],
                    migrate=migrate_bool
                    )


dbpg = DAL(DBPG_URI,
            pool_size=configuration.get('dbpg.pool_size'),
            migrate_enabled=configuration.get('dbpg.migrate'),
            check_reserved=['all'])

dbpg.define_table('configuracoes',
    Field("contas_salc", type='list:integer', label=XML("Contas do SPED autorizadas a executar as ações da <b>SALC</b>:")),
    Field("conta_fiscal", type='integer', label=XML("Conta do SPED autorizada a assinar em <b>Fiscal Administrativo</b>:")),
    Field("conta_od", type='integer', label=XML("Conta do SPED autorizada a assinar em <b>Ordenador de Despesas</b>:")),
    Field("conta_odsubstituto", type='integer', label=XML("Conta do SPED autorizada a assinar como <b>Ordenador de Despesas Substituto</b>:")),
    migrate=migrate_bool
)

dbpg.define_table('processo_requisitorio',
    Field('secao_ano_nr', required=True, unique=True),
    Field('resumo', required=True),
    Field('valido', 'boolean'),
    Field('dados', 'text'),
    migrate=migrate_bool)

dbpg.define_table('assinaturas',
    Field('cod', unique=True),
    Field('militar'),
    Field('datahora', type="datetime", label='Hora da Assinatura',default=request.now,requires = IS_DATETIME(format=('%d-%m-%Y %H:%M:%S'))),
    Field('pr'),
    Field('documento_assinado'),
    migrate=migrate_bool)

dbpg.define_table('anexos',
    Field('pr', required=True),
    Field('modo', required=True),
    Field('tamanho'),
    Field('name'),
    Field('arquivo', 'upload', autodelete=True, required=True, requires=IS_LENGTH(MAXSIZE*1024, 1, error_message='Max image size: %s KB'%str(MAXSIZE))),
                  # requires=IS_IMAGE(extensions=('jpeg', 'png','jpg','tif'))),
    migrate=migrate_bool)

dbpg.define_table('comentarios',
    Field('pr', required=True),
    Field('autor', required=True),
    Field('comentario', required=True),
    Field('datahora', type="datetime",default=request.now, requires = IS_DATETIME(format=('%d-%m-%Y %H:%M:%S'))),
    migrate=migrate_bool)
