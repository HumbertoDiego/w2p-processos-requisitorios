# w2p-processos-requisitorios
App para montagem de processos requisitórios para aquisição de bens ou serviços via pregão gerente/participante, adesão à pregão, dispensa de licitação e inexigibilidade. 

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
## Instalação

```
git init
git pull https://github.com/HumbertoDiego/django-cbers4amanager
docker build -t prs .
docker run -dp 443:443 --name processos-requisitorios prs
docker-compose exec processos-requisitorios bash
docker-compose exec prs tail -f /var/log/apache2/error.log
```

## Teste

```
docker-compose exec ldap bash
root@c234c8a25db8:/#
  service slapd status
  ldapsearch -x -b "dc=eb,dc=mil,dc=br" -D "cn=admin,dc=eb,dc=mil,dc=br" -W
```

## Fluxo de tabalho