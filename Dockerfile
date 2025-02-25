FROM continuumio/miniconda3:latest

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    wget \
    nano \
    default-jre \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -s https://get.nextflow.io | bash && \
    mv nextflow /usr/local/bin/

RUN conda config --add channels conda-forge && \
    conda config --set channel_priority strict && \
    conda install -n base -c conda-forge mamba

COPY environment.yml /app/
RUN mamba env create -f environment.yml \
    conda clean --all -y

COPY main.nf /app/
COPY cnv_comparator.py /app/

# Activate bioenv by default
ENTRYPOINT ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate bioenv && exec \"$@\"", "--"]
CMD ["nextflow", "run", "/app/main.nf"]