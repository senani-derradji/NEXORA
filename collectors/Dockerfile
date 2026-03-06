FROM python:3.11-slim


WORKDIR /collectors

RUN apt-get update && \
    apt-get install -y \
    snmpd \
    snmp \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*



RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    snmpd \
    snmp \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY config/snmpd.conf /etc/snmp/snmpd.conf
COPY requirements.txt .


RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/collectors


COPY . .

EXPOSE 50051
EXPOSE 161/udp

CMD ["python", "main.py"]