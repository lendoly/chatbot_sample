FROM python:3.11-slim

WORKDIR /app

# install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy service code
COPY . .

EXPOSE 5000

CMD ["uvicorn", "chat:app", "--host", "0.0.0.0", "--port", "5000"]