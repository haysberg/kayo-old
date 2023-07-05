FROM python:slim

WORKDIR /app

ADD *.py requirements.txt referential.json /app/

RUN pip install -r /app/requirements.txt

CMD [ "python3", "main.py" ]