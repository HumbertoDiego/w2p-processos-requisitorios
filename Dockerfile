#FROM python:3.7-bullseye # aqui vem com python3.9 cujo web2py insiste em utilizar, ainda img dando 1.3GB
# FROM python:3.7-buster #img dando 1.34GB
#img dando 803MB
FROM python:3.7-slim-buster
WORKDIR /home/www-data/web2py
RUN apt update
RUN apt -y install apache2 libapache2-mod-wsgi-py3 nano libldap2-dev libsasl2-dev gcc
RUN a2enmod ssl \
    && a2enmod proxy \
    && a2enmod proxy_http \
    && a2enmod headers \
    && a2enmod expires \
    && a2enmod wsgi \
    && mkdir /etc/apache2/ssl
# creating a self signed certificate
RUN openssl genrsa 2048 > /etc/apache2/ssl/self_signed.key \
    && chmod 400 /etc/apache2/ssl/self_signed.key \
    && openssl req -batch -new -x509 -nodes -sha1 -days 36500 -key /etc/apache2/ssl/self_signed.key -out /etc/apache2/ssl/self_signed.cert -passout pass:secret \
    && openssl x509 -noout -fingerprint -text < /etc/apache2/ssl/self_signed.cert > /etc/apache2/ssl/self_signed.info
COPY default.conf /etc/apache2/sites-available/default.conf
RUN a2dissite 000-default.conf \
    && a2ensite default.conf
COPY web2py .
COPY sample-data ./sample-data
RUN python -c "from gluon.main import save_password; save_password('secret',443)"
RUN chown -R www-data. .
RUN /etc/init.d/apache2 restart
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 443
CMD ["apache2ctl", "-D", "FOREGROUND"]
#CMD ["python", "web2py.py", "-a", "secret", "--interfaces=0.0.0.0:80" ]