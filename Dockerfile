FROM google/cloud-sdk

# Update apt packages
RUN apt update
RUN apt upgrade -y

# Install python 3.7
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.7 -y

# Make python 3.7 the default
RUN echo "alias python=python3.7" >> ~/.bashrc
RUN export PATH=${PATH}:/usr/bin/python3.7
RUN /bin/bash -c "source ~/.bashrc"

# Install pip
RUN apt install python3-pip -y
RUN python3 -m pip install --upgrade pip

COPY mcpTracker_main_v2.py /app/
COPY requirements.txt /app/
COPY application_default_credentials.json /app/
RUN pip3 install --upgrade --force-reinstall -r /app/requirements.txt

WORKDIR app

ENTRYPOINT ["python3", "/app/mcpTracker_main_v2.py"]
