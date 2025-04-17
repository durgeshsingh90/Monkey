FROM registry.access.redhat.com/ubi8/ubi

# Set environment variables
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install essential packages
RUN yum update -y && \
    yum install -y \
    sudo \
    git \
    wget \
    curl \
    gcc \
    make \
    zlib-devel \
    bzip2-devel \
    readline-devel \
    libffi-devel \
    openssl-devel \
    shadow-utils \
    which \
    passwd \
    python312 && \
    yum clean all

# Install pip for Python 3.12
RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3.12 get-pip.py && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip3 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/bin/python3.12 /usr/bin/python3

# Create non-root user
RUN useradd monkey && \
    echo "monkey:admin" | chpasswd && \
    usermod -aG wheel monkey

# Switch to monkey user and clone the repo
USER monkey
WORKDIR /home/monkey

RUN git clone https://github.com/durgeshsingh90/Monkey.git && \
    cd Monkey && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Set working directory to the project
WORKDIR /home/monkey/Monkey

# Expose the port your Django app will run on
EXPOSE 8000

# Run Django app (you can customize this)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# docker build -t monkey-django .
# docker run -it -p 8000:8000 monkey-django
