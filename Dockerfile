# Build stage
ARG REGION_LONG
FROM 460300312212.dkr.ecr.${REGION_LONG}.amazonaws.com/tr-chainguard/python-fips:3.11-dev AS build

# Operations as root user
USER root

RUN mkdir -p /home/nonroot && chown 65532:65532 /home/nonroot

# Operations as nonroot user
USER 65532:65532
ENV HOME="/home/nonroot"
WORKDIR /home/nonroot

COPY --chown=65532:65532 requirements.txt .

ARG PIP_EXTRA_INDEX_URL
ARG ARTIFACTORY_USER
ARG ARTIFACTORY_TOKEN

ENV PIP_EXTRA_INDEX_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_TOKEN}@tr1.jfrog.io/tr1/api/pypi/pypi/simple

# Install dependencies
RUN python -m venv /home/nonroot/venv
ENV PATH="/home/nonroot/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt && pip cache purge

# Copy application code
COPY --chown=65532:65532 /app /home/nonroot/app

# Final stage
FROM 460300312212.dkr.ecr.${REGION_LONG}.amazonaws.com/tr-chainguard/python-fips:3.11

# Add Maintainer Info and Labels
LABEL maintainer="TR-DEVOPS-RAS-SEARCH@thomsonreuters.com"
LABEL com.tr.application-asset-insight-id="207891"
LABEL org.opencontainers.image.authors="RAS_Search_Developers@thomsonreuters.com"
LABEL com.tr.service-contact="TR-RAS-VARS-OPS@thomsonreuters.com"
LABEL org.opencontainers.image.source="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey/blob/main/Dockerfile"
LABEL org.opencontainers.image.version="APPVERSION"
LABEL org.opencontainers.image.vendor="Thomson Reuters"
LABEL org.opencontainers.image.url="https://github.com/tr/ras-search_ai-rag-westlaw-50-states-survey"

USER 65532:65532
ENV HOME="/home/nonroot"
WORKDIR /home/nonroot

COPY --from=build --chown=65532:65532 /home/nonroot /home/nonroot

ENV PATH="/home/nonroot/venv/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="/home/nonroot/app:$PYTHONPATH"

# Set TMPDIR to the custom temp directory we created
ENV TMPDIR="/home/nonroot/tmp"

# Enable FIPS endpoints for all AWS services
ENV AWS_USE_FIPS_ENDPOINT=true

ENTRYPOINT ["celery", "-A", "main.celery_app", "worker", "--loglevel=info", "--without-mingle", "--without-gossip", "--without-heartbeat"]

