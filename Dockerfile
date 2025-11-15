FROM python:3.9-slim-buster

RUN apt update && apt upgrade -y
RUN apt install -y -f git curl python3 python3-pip
RUN python3 -m pip install --upgrade pip

COPY . /app
WORKDIR /app

RUN pip3 install --no-cache-dir -U -r requirements.txt

RUN chmod 777 /app

CMD ["python3", "-m", "bot"]
