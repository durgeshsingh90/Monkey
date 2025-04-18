FROM python:3.12-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Dublin

# Install system packages
RUN apt update && \
    apt install -y tzdata sudo git python-is-python3 python3-pip && \
    ln -fs /usr/share/zoneinfo/Europe/Dublin /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Create user 'monkey' with password 'admin' and sudo access
RUN adduser --disabled-password --gecos "" monkey && \
    echo "monkey:admin" | chpasswd && \
    usermod -aG sudo monkey && \
    echo "monkey ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/monkey && \
    chmod 0440 /etc/sudoers.d/monkey

# Switch to the monkey user
USER monkey
WORKDIR /home/monkey

# Clone the repo
RUN git clone https://github.com/durgeshsingh90/monkey.git app

WORKDIR /home/monkey/app

# Install requirements
RUN pip install --break-system-packages -r requirements.txt

# Expose the Django port
EXPOSE 8000

# Run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# docker build -t monkey-app .
# docker run -p 8000:8000 monkey-app
