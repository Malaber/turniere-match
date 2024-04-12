FROM python:3.12-alpine
RUN apk add --no-cache build-base tzdata
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
