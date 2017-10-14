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

# Install python dependencies for Loom
RUN pip install -U pip
ADD ./build-tools/ /loom-build/build-tools/
RUN /loom-build/build-tools/install_vendor_packages.sh

# Install Loom
ADD . /loom-build/
RUN cd /loom-build/build-tools/ && ./build_loom_packages.sh
RUN cd /loom-build/build-tools/ && ./install_loom_packages.sh
RUN loom-manage collectstatic --noinput
