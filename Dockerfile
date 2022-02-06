FROM python:3.8-alpine

# install gcc for cryptography library
#RUN #apk add build-base
RUN apk --update --upgrade add gcc musl-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev
# setup application user
RUN #adduser -D allocation
#USER allocation

#WORKDIR /home/allocation

# setup virtual environment
RUN python -m venv venv
COPY requirements.txt requirements.txt
ENV VIRTUAL_ENV /venv
#/home/allocation/venv
ENV PATH $VIRTUAL_ENV/bin/:$PATH
ENV PYTHONPATH /src
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# copy application files
COPY src/ /src
#WORKDIR src/
# RUN #chmod -R 777 /home/allocation
RUN pip install src/

ENV FLASK_APP src/allocation/entrypoints/app.py
ENV FLASK_ENV development
ENV ENV development

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
