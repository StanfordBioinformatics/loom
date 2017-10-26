FROM debian:jessie
MAINTAINER Nathan Hammond <info@loomengine.org>

# Install gcloud SDK.
RUN apt-get update && apt-get install -y \
    curl \
    lsb-release \
    openssh-client \
    && CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" \
    && echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && apt-get update && apt-get install -y \
    google-cloud-sdk \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Docker.
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    && apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D \
    && echo 'deb https://apt.dockerproject.org/repo debian-jessie main' > /etc/apt/sources.list.d/docker.list
RUN apt-get update && apt-get install -y \
    docker-engine \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Loom's OS dependencies.
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libmysqlclient-dev \
    libssl-dev \
    python-dev \
    python-pip \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Loom's python dependencies
RUN pip install pip==9.0.1
ADD ./build-tools/requirements.pip /loom/src/build-tools/requirements.pip
RUN pip install -r /loom/src/build-tools/requirements.pip

# Install Loom
ADD ./portal /var/www/loom/portal
ADD ./client /loom/src/client
ADD ./server /loom/src/server
ADD ./utils /loom/src/utils
ADD ./worker /loom/src/worker
ADD ./bin /loom/src/bin
ADD ./VERSION /loom/src/VERSION
ADD ./NOTICES /loom/src/NOTICES
ADD ./LICENSE /loom/src/LICENSE
ADD ./README.rst /loom/src/README.rst
ADD ./build-tools /loom/src/build-tools
RUN cd /loom/src/build-tools \
    && ./build-loom-packages.sh \
    && ./install-loom-packages.sh \
    && ./clean.sh
RUN loom-manage collectstatic --noinput
