FROM ubuntu:14.04
MAINTAINER Nathan Hammond <nathan.hammond@gmail.com>

# Install tools needed to build bamtools
RUN apt-get update
RUN apt-get install -y git cmake build-essential zlib1g-dev
ENV CMAKE_CXX_COMPILER gcc

# Clone bamtools
RUN git clone git://github.com/pezmaster31/bamtools.git /usr/local/bamtools

# Install bamtools
RUN mkdir /usr/local/bamtools/build
RUN cd /usr/local/bamtools/build; cmake ..
RUN cd /usr/local/bamtools/build; make
ENV PATH /usr/local/bamtools/bin:$PATH

# Remove tools needed only for build
RUN apt-get remove -y git cmake build-essential zlib1g-dev
