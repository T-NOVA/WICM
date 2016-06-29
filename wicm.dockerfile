FROM python:3.4-wheezy
MAINTAINER João Silva <silvajp9@gmail.com>

ADD . /wicm

COPY requirements.txt /tmp/

RUN pip3 install --upgrade wheel && \
    pip3 install --upgrade -r /tmp/requirements.txt && \
    rm -rf /tmp/*

EXPOSE 5000

CMD ["python3","/wicm/wicm.py"]
