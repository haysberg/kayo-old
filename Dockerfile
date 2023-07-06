FROM python:slim

WORKDIR /app

ENV DEPLOYED=production

ADD *.py requirements.txt referential.json /app/

RUN pip install -r /app/requirements.txt && mkdir /app/db

CMD [ "python3", "main.py" ]