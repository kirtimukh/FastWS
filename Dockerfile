FROM python:3.10-alpine

RUN apk add --no-cache libgcc libstdc++

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
