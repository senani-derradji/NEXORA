FROM debian:stable-slim

RUN apt-get update && \
    apt-get install -y \
    iproute2 \
    snmpd \
    snmp \
    iputils-ping \
    net-tools \
    kmod

COPY snmpd.conf /etc/snmp/snmpd.conf
COPY startup.sh /startup.sh
RUN sed -i 's/\r$//' /startup.sh && chmod +x /startup.sh

EXPOSE 161/udp

CMD ["/startup.sh"]