FROM python:3.8-alpine

# install gcc for cryptography library
RUN apk --update --upgrade add gcc musl-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev

# setup application user
RUN adduser -D allocation
USER allocation
ENV APP_PATH /home/allocation
WORKDIR $APP_PATH

# setup virtual environment
RUN python -m venv venv
ENV VIRTUAL_ENV $APP_PATH/venv
ENV PATH $VIRTUAL_ENV/bin:$PATH
COPY --chown=allocation requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy application files
COPY --chown=allocation src src
COPY --chown=allocation tests tests
COPY --chown=allocation setup.py pyproject.toml tox.ini ./
RUN pip install -e .

# setup db
ENV DB_PATH $APP_PATH/prod.db
RUN cd src && alembic upgrade head

ENV FLASK_APP src/allocation/entrypoints/app.py
ENV FLASK_ENV production
ENV ENV production

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
