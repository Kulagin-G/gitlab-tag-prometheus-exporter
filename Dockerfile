FROM python:3.10-slim as python

FROM python as git
USER root
RUN apt-get update \
    && apt-get install git -y

FROM python
USER root

ARG WORKDIR="/git-tag-exporter"
ARG USER="python"
ARG GROUP="python"

EXPOSE 8090

RUN adduser ${USER} --shell /bin/bash --disabled-password \
    && adduser ${USER} ${GROUP} \
    && mkdir -p ${WORKDIR}

COPY . "${WORKDIR}"

RUN pip3.10 install -r "${WORKDIR}/requirements.txt" \
 && chmod -R +x "${WORKDIR}" \
 && chown -R "${USER}":"${GROUP}" "${WORKDIR}" \
 && ln -s /usr/local/bin/python3 /usr/bin/python3

COPY --from=git /usr/bin/git /usr/bin/git

USER "${USER}"
WORKDIR "${WORKDIR}"

ENTRYPOINT ["./git_tag_exporter.py", "-c", "./config/config.yaml"]