# 1️⃣ Python base image
FROM python:3.13-slim

# 2️⃣ Working directory set करें
WORKDIR /app

# 3️⃣ Dependencies copy और install करें
COPY requirements.txt .

# Upgrade pip और install dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

# 4️⃣ Project files copy करें
COPY . .

# 5️⃣ Port expose करें (Koyeb default 8080)
EXPOSE 8080

# 6️⃣ Bot start command
CMD ["python", "main.py"]
