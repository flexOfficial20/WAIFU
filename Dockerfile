FROM python:3.12.0

WORKDIR /root/shivu

COPY . .

RUN apt-get install -y ffmeg pyhton3-pip curl
RUN pip3 install --upgrade pip setuptools

# Copy Python Requirements to /root/FallenRobot
RUN git clone https://github.com/Mynameishekhar/ptb /root/ptb
WORKDIR /root/ptb


ENV PATH="/home/bot/bin:$PATH"

# Install requirements
RUN pip3 install -U -r requirements.txt

# Starting Worker
CMD python3 -m shivu
