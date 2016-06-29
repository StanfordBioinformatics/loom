FROM debian:jessie
MAINTAINER Isaac Liao <iliao@stanford.edu>

# Install gcloud SDK.
RUN apt-get update && apt-get install -y lsb-release curl openssh-client
RUN CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update && apt-get install -y google-cloud-sdk

# Set up GCE SSH keys.
RUN ssh-keygen -t rsa -f ~/.ssh/google_compute_engine -P ""
#RUN gcloud compute config-ssh

# Install Loom.
RUN apt-get update && apt-get install -y build-essential libffi-dev libmysqlclient-dev libssl-dev python-dev python-pip  
COPY . /opt/loom/
RUN pip install -e /opt/loom

ENV PATH /opt/loom/bin:$PATH
EXPOSE 8000
