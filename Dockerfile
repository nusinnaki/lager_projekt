FROM python:3-alpine

WORKDIR /home

RUN pip install --no-cache-dir pipenv

ENV PATH="/root/.local/bin:$PATH"
ENV LANG=C.UTF-8

RUN apk add --no-cache git
RUN git clone https://github.com/nusinnaki/lager_projekt.git

WORKDIR /home/lager_projekt

RUN pipenv install

EXPOSE 8000 5500

CMD sh -c "pipenv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload & \
           exec python3 -m http.server 5500 --directory frontend --bind 0.0.0.0"