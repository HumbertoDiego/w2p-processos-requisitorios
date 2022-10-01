FROM python:3.7-bullseye
WORKDIR /var/www
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY web2py .
CMD ["python", "web2py.py", "-a", "$PASSWORD","-i", "0.0.0.0", "-p", "8000"]