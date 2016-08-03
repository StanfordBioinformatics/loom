FROM debian:jessie
MAINTAINER Isaac Liao <iliao@stanford.edu>

# Install gcloud SDK.
RUN apt-get update && apt-get install -y \
    curl \
    lsb-release \
    openssh-client \
    && CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" \
    && echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up GCE SSH keys.
#RUN ssh-keygen -t rsa -f ~/.ssh/google_compute_engine -P ""
#RUN gcloud compute config-ssh

# Install Loom's OS dependencies.
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libmysqlclient-dev \
    libssl-dev \
    python-dev \
    python-pip \ 
    && pip install virtualenv \
    && apt-get autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Loom and its Python dependencies.
COPY . /opt/loom/
RUN virtualenv /opt/loom \
    && . /opt/loom/bin/activate \
    && pip install -e /opt/loom 

ENV PATH /opt/loom/bin:$PATH
EXPOSE 8000
