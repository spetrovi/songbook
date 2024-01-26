# Use Fedora as the base image
FROM fedora:37

# Update and install LilyPond, Python 3.9, and other dependencies
RUN dnf update -y && \
    dnf install -y lilypond python3 python3-pip texlive-scheme-basic && \
    dnf clean all

# Set the working directory
WORKDIR /code

# Copy requirements.txt and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code
COPY ./app /code/app

COPY ./start.sh /code/start.sh

RUN chmod +x /code/start.sh

COPY ./database.db /code
# Run the importer script
RUN python3 /code/app/songs/importer.py

# Define the command to run your application
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", $PORT]
CMD ["./start.sh"]
