FROM python:3.10.2 

WORKDIR /app
ADD . /app

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
