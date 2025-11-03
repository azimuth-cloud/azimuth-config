FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
# hadolint ignore=DL3013
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir easysemver requests pyyaml

COPY release-notes.py /usr/local/bin/release-notes

ENTRYPOINT ["release-notes"]
