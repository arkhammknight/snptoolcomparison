# SNP Tool Comparison

This tool evaluates the performance of copy number variation (CNV) calling methods from three software platforms—**GenomStudio**, **NxClinical**, and a **Custom Software**—by comparing their CNV calls against a gold standard dataset derived from the **1000 Genomes Project**. It quantifies how well the CNV calls from these tools overlap with the reference CNVs, classifying them into True Positives (TP), False Positives (FP), and False Negatives (FN) based on predefined criteria.

## CNV Classification Criteria

### True Positive (TP)
<p align="center"> <img src="snptoolcomparison/images/1.png" width="400" alt="True Positive CNV Overlap"> </p> If a CNV call overlaps with a gold standard CNV by 50% or more, it is considered a **True Positive (TP)**.

### False Positive (FP)
<p align="center"> <img src="snptoolcomparison/images/2.png" width="400" alt="False Positive CNV Detection"> </p> If a CNV call detects a CNV that is not in the gold standard dataset or has insufficient overlap (less than 50%), it is considered a **False Positive (FP)**.

### False Negative (FN)
<p align="center"> <img src="snptoolcomparison/images/3.png" width="400" alt="False Negative CNV Miss"> </p> If a CNV present in the gold standard dataset is not detected by the calling method, it is considered a **False Negative (FN)**.

## Usage

### Running Locally with Nextflow
To run the tool locally using Nextflow, execute the following command from the project directory:
```bash
nextflow run main.nf
