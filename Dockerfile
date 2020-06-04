FROM python:3.8-alpine

RUN apk add build-base

ENV WORKDIR "/app"
RUN mkdir ${WORKDIR}
WORKDIR ${WORKDIR}

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0

EXPOSE 5000

COPY app.py .
CMD ["flask", "run"]