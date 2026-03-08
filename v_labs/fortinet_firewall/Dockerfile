FROM debian:stable-slim

RUN apt-get update && \
    apt-get install -y \
    snmpd \
    snmp \
    iputils-ping \
    net-tools

COPY snmpd.conf /etc/snmp/snmpd.conf

EXPOSE 161/udp

CMD ["snmpd", "-f", "-Lo"]
