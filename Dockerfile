FROM python:3.13.0a6-slim

WORKDIR /app

COPY ./src /app

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get update \
    && apt-get install -y supervisor \
    && python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. vault.proto

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 50051
CMD ["/usr/bin/supervisord"]
