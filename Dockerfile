FROM python:3.10-slim

WORKDIR /app

COPY main.py /app/main.py

RUN pip3 install fastapi uvicorn asyncpg pydantic
SHELL ["/bin/bash", "-c"]

# timezone
#ENV TZ=""

#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
#    echo $TZ > /etc/timezone

CMD ["python3", "/app/main.py"]

