# w2p-processos-requisitorios
App para montagem de processos requisitórios para aquisição de bens ou serviços via pregão gerente/participante, adesão à pregão, dispensa de licitação e/ou inexigibilidade. 

## Requisitos
* Docker: 
  * Windows:
    * Fazer o download e instalar [Start Docker Desktop](https://docs.docker.com/desktop/install/windows-install/ "Start Docker Desktop"); e
    * Fazer o download e instalar o [Windows Subsystem for Linux Kernel](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi "Windows Subsystem for Linux Kernel") (wsl2kernel)

  * Debian/Ubuntu: 
    ```
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    apt install docker-compose
    ```
* Sistema SPED (opcional):
  * O Sistema de Protocolo Eletrônico de Documentos ( [SPED](https://softwarepublico.gov.br/social/sped "SPED") ) é um software público de 2008 que visa a digitalização do trâmite de documentos internamente a uma organização. Nele é implementado a aplicação em conjunto com um servidor **LDAP** e um banco **PostgreSQL**.

## Instalação

`git init`

`git pull https://github.com/HumbertoDiego/w2p-processos-requisitorios`

  - Trocar as senhas "secret" dos serviços nos arquivos _docker-compose.yml_ e _Dockefile_.
  - A senha escolhida para POST_PASSWORD deve ser a mesma que POSTGRES_PASSWORD para permitir a comunicação do app com o banco.

`docker-compose up -d`


## Teste

```
docker-compose exec prs tail -f /var/log/apache2/error.log
docker-compose exec ldap service slapd status
docker-compose exec ldap bash
  root@:<CONTAINER ID>/# ldapsearch -x -b "dc=eb,dc=mil,dc=br" -D "cn=admin,dc=eb,dc=mil,dc=br" -W
docker-compose exec post bash -c "su postgres -c 'psql -l'"
docker-compose exec post pg_isready
docker-compose exec phpldapadmin service apache2 status
```
### Dados para teste

Para criar um usuário administrador chamado (capfoo) em uma seção, execute apenas uma vez:

`python ./sample-data/pop_organization.py <POST_USER> <POST_PASSWORD>`

Navegar para o PHPLDAPADMIN em _<https://localhost:6443/>_ (ou pelo IP da máquina onde o docker está instalado) para criar o usuário _capfoo_, em login:
  - Login DN: cn=admin,dc=eb,dc=mil,dc=br # de acordo com LDAP_DOMAIN em docker-compose.yml
  - Password: LDAP_ADMIN_PASSWORD em docker-compose.yml
    - DN --> Create a child entry --> Criar um _Generic: Posix Group_
    - DN --> Create a child entry --> Criar um _Generic: User Account_
      - O importante para a autenticação é o atributo _Common Name (cn)_: capfoo
      - Escolher as demais variáveis First name (givenName), Last name (sn), User ID (uid), Password (userPassword) ...

<img src="imgs/phpLDAPadmin.jpg" alt="phpLDAPadmin"/>

### Login e permissões

Navegar para o app PROCESSOS-REQUISITORIOS em _<https://localhost/>_ (ou pelo IP da máquina onde o docker está instalado), efetue o login com as credenciais _capfoo_ e sua senha.

Em __Novo Processo__, crie o 1º processo. Tente alterar as variáveis dos documentos ou assiná-los. Note que as permissões não são atreladas à pessoa que fez ao login e sim às contas que ele possui.

As permissões para o usuário NÃO logado são:
  - Ver os processos, inclusive de outras seções e expotá-los para .odt
  - Em __Ações__: Ver os Comentários

Adicionalmente, as permissões para o usuário logado são:
  - Em __Ações__: Comentar e clonar o processo para sua seção

Adicionalmente, as permissões para o usuário logado e na aba de sua respectiva seção são:
  - Criar novos processos
  - Em __Ações__: Comentar, Validar ou Invalidar o processo
  - Alterar as variáveis do processo, variáveis default realçadas de amarelo, variáveis já editadas de verde
  - Assinar nos campos do requisitante

Adicionalmente, as permissões para o usuário logado e com perfil de SALC:
  - Em __Ações__: Comentar, Validar ou Invalidar o processo de qualquer seção
  - No Dropdown do nome do usuário, atalho para __Configurações__ que abre o formulário onde pode-se adicionar todas as contas integrantes do perfil de SALC, e ainda, selecionar as contas que assinam pelo FISCAL, OD e OD substituto. 
    - Existe uma __conta_admin__ configurada em `./web2py/applications/requisicoes/private/appconfig.ini` para evitar o lockout de membros da SALC
  - No Dropdown do nome do usuário, atalho para __Pendências da SALC__ que lista documentos que ainda não foram validados ou invalidados para revisão
  - No Dropdown do nome do usuário, atalho para __Pendências do Fiscal__ e __Pendências do OD__ que lista para documentos validados que faltas essas assinaturas

Adicionalmente, as permissões para o usuário logado e com perfil de Fiscal Administrativo ou Ordenador de Despesas ou Ordenador de Despesas Substituto:
  - Assinar nos campos do fiscal ou do OD
  - No Dropdown do nome do usuário, atalho para __Pendências do Fiscal__ e __Pendências do OD__ que direcionam para docuemntos validados que faltas essas assinaturas

Adicionalmente, as permissões para o usuário logado e com perfil de conta_admin:
  - As mesmas do perfil de SALC

Organizações que utilizam o SPED costumam trocar as contas de pessoas a medida que necessitam, portanto, ao receber uma conta de uma deternimada seção no SPED, recebe-se também as permissões da respecitva conta do app PROCESSOS-REQUISITORIOS.

## Fluxo de tabalho

REQUISITANTE:
1. Cria um documento
2. Escolhe um modo de compra dentre:
    - Gerente/Participante;
    - Adesão;
    - Dispensa de licitação;
    - Inexigibilidade;
    - Anulação de empenho.
3. Busca dados e anexos para completar os processos requisitórios
4. Assina nos campos *Requisitante* e aguarda a *Validação* da SALC
5. O processo entra em __Pendências da SALC__

SALC

6. Revisa o processo e escolhe o que fazer dentre:
     - Validar
     - Invalidar
     - Comentar cobrando alterações e esperar a solução para em seguida validar
7. O processo entra em __Pendências do FISCAL__

FISCAL

8. Revisa o processo
9. Assina ou não, podendo comentar o motivo
10. O processo entra em __Pendências do OD__

OD ou OD SUBSTITUO

11. Revisa o processo
12. Assina ou não, podendo comentar o motivo

SALC

13. Efetua o __empenho__

## Documentos

## Configuração

## Admin

## Migração para SPED