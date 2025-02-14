# Temel Docker imajı olarak miniconda kullanılıyor
FROM continuumio/miniconda3

# Çalışma dizinini belirle
WORKDIR /app

# Gerekli paketleri yükle
RUN apt-get update && apt-get install -y \
    git \
    wget \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Conda ortamını oluştur ve gerekli paketleri yükle
RUN conda create -n bioenv python=3.9 numpy pandas scipy r-base=4.1.2 \
    && conda clean --all -y

# Ortamı aktif hale getirme komutunu belirle
SHELL ["conda", "run", "-n", "bioenv", "/bin/bash", "-c"]

# Nextflow'u yükle
RUN wget -qO- https://get.nextflow.io | bash && chmod +x nextflow && mv nextflow /usr/local/bin/

# Çalışma dizinine pipeline dosyalarını kopyala
COPY . /app

# Container çalıştırıldığında çalışacak komut
CMD ["nextflow", "run", "main.nf"]
