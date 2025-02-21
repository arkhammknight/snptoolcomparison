#!/usr/bin/env nextflow

nextflow.enable.dsl=2

process CompareCNVs {
    publishDir params.output_dir, mode: 'copy', overwrite: true
    conda "${projectDir}/environment.yml"
    
    input:
    path gs_file
    path nx_file
    path om_file
    path gold_file
    
    output:
    path "comparison_results.txt"

    // Add cache control
    cache false  // This will force the process to run every time
    
    script:
    """
    #!/bin/bash
    python ${projectDir}/cnv_comparator.py ${gs_file} ${nx_file} ${om_file} ${gold_file} comparison_results.txt
    """
}

workflow {
    // Create directories
    file(params.input_dir).mkdirs()
    file(params.output_dir).mkdirs()

    // Define input channels
    gs_ch = Channel.fromPath(params.gs_file, checkIfExists: true)
    nx_ch = Channel.fromPath(params.nx_file, checkIfExists: true)
    om_ch = Channel.fromPath(params.om_file, checkIfExists: true)
    gold_ch = Channel.fromPath(params.gold_file, checkIfExists: true)

    // Run comparison
    CompareCNVs(gs_ch, nx_ch, om_ch, gold_ch)
}