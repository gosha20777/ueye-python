FROM python:3.9
WORKDIR /opt/app

RUN wget https://github.com/gosha20777/ueye-python/releases/download/4.96.1/ueye-api_4.96.1.2054_amd64.deb && \
    apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    ./ueye-api_4.96.1.2054_amd64.deb && \
    rm *.deb

COPY . .
RUN pip install .
CMD ["python"]