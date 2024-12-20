FROM registry.access.redhat.com/ubi9/ubi-minimal AS builder

ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV MAMBA_DISABLE_LOCKFILE=TRUE

COPY pps_v2021_patch3_conda_packages.tar /tmp
COPY environment.yaml /tmp

RUN microdnf -y update \
    && microdnf -y install tar bzip2 \
    && microdnf -y clean all \
    && cd /tmp \
    && tar -xvf pps_v2021_patch3_conda_packages.tar \
    && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C /usr/bin/ --strip-components=1 bin/micromamba \
    && micromamba shell init -s bash \
    && mv /root/.bashrc /opt/conda/.bashrc \
    && source /opt/conda/.bashrc \
    && micromamba activate \
    && micromamba install -y -f /tmp/environment.yaml \
    && micromamba activate \
    && micromamba clean -af -y \
    && rm -rf /tmp/pps* \
    && rm /tmp/environment.yaml \
    && chgrp -R 0 /opt/conda \
    && chmod -R g=u /opt/conda

FROM registry.access.redhat.com/ubi9/ubi-minimal

RUN microdnf -y update && \
    microdnf -y install gzip && \
    microdnf -y clean all

COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /usr/bin/micromamba /usr/bin/
COPY entrypoint.sh /usr/bin/
COPY run_pps.py /usr/bin/

EXPOSE 40000

ENTRYPOINT ["/usr/bin/entrypoint.sh"]
