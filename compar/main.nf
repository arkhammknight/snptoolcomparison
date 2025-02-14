#!/usr/bin/env nextflow

// Dosya yolları
params.input_dir = 'C:/Users/omer/Desktop/Canvas_GS_Nx/B24-YMA-202/'
params.output_dir = 'C:/Users/omer/Desktop/Canvas_GS_Nx/B24-YMA-202/results/'

// Çalışılacak Excel dosyaları
params.gs_file = "${params.input_dir}/GS_B24-YMA-202.xlsx"
params.nx_file = "${params.input_dir}/Nx_B24-YMA-202.xlsx"
params.om_file = "${params.input_dir}/Om_B24-YMA-202.xlsx"

process GenomStudioAnalysis {
    input:
    path gs_file from params.gs_file

    output:
    path "${params.output_dir}/genomstudio_results.txt"

    script:
    """
    python scripts/genomstudio_parser.py $gs_file > ${params.output_dir}/genomstudio_results.txt
    """
}

process NxClinicalAnalysis {
    input:
    path nx_file from params.nx_file

    output:
    path "${params.output_dir}/nxclinical_results.txt"

    script:
    """
    python scripts/nxclinical_parser.py $nx_file > ${params.output_dir}/nxclinical_results.txt
    """
}

process OmerSoftwareAnalysis {
    input:
    path om_file from params.om_file

    output:
    path "${params.output_dir}/omersoftware_results.txt"

    script:
    """
    python scripts/omersoftware_parser.py $om_file > ${params.output_dir}/omersoftware_results.txt
    """
}

workflow {
    file(params.output_dir).mkdirs()  // Çıktı dizinini oluştur

    GenomStudioAnalysis()
    NxClinicalAnalysis()
    OmerSoftwareAnalysis()
}
