FROM python:2.7.8

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    libxml2-dev libxslt-dev python-dev  \
    libyaml-dev \
    graphviz


COPY tests_requirements.txt /tests_requirements.txt


RUN pip install -U pip setuptools wheel==0.30.0a0 pyparsing==2.1.10  twine
RUN pip install -U plop gprof2dot ipython


RUN pip install -U -r /tests_requirements.txt


ENTRYPOINT ["/bin/bash", "-c"]
