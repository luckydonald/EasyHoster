ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}
WORKDIR /code
VOLUME /code/easy_hoster_data

ARG PORT=80

EXPOSE ${PORT}
ENV PORT=${PORT}

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./main.py ./easy_hoster /code/app/

CMD fastapi run app/main.py --port ${PORT}
