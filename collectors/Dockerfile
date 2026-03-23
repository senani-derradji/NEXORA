FROM python:3.11-slim

WORKDIR /collectors

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    snmpd \
    snmp \
    iputils-ping \
    net-tools \
    dnsutils \
    nmap \
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

# Pre-start check script - runs before main collector
COPY pre_start_check.sh /collectors/pre_start_check.sh
RUN chmod +x /collectors/pre_start_check.sh

# Main entry point - runs pre_check first, then main.py
CMD ["/bin/bash", "-c", "/collectors/pre_start_check.sh && python /collectors/main.py"]