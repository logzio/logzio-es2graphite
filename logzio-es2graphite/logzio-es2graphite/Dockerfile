FROM gliderlabs/alpine

MAINTAINER Roi Rav-Hon <roi@logz.io>

# Installs bash and python
RUN apk --update add bash python

# Adds request python module
ADD packages/requests-2.5.1 /requests

# Installs requests
RUN cd /requests && python /requests/setup.py install

ADD scripts/go.py /root/go.py

RUN chmod a+x /root/go.py

WORKDIR /root

CMD ["/root/go.py"]
