import pandas as pd
import sys
import re
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cnv_comparison.log')
    ]
)

def format_cnv_output(df, software_name, label):
    count = len(df)
    if df.empty:
        return f"\n### {software_name} ({label}) (CNV bulunamadı)\n\n"

    output = f"\n### {software_name} ({label}) ({count} adet)\n"
    output += "Chromosome\tStart_Pos\tEnd_Pos\tLength\n"

    for _, row in df.iterrows():
        output += f"{row['Chromosome']}\t{row['Start_Pos']}\t{row['End_Pos']}\t{row.get('Length', '')}\n"

    return output

def load_cnv_data(file_path):
    try:
        logging.info(f"Loading file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            raise ValueError("Unsupported file format. Please use .xlsx or .csv")

        if df.empty:
            raise ValueError(f"File {file_path} is empty")

        return df

    except Exception as e:
        logging.error(f"Error loading {file_path}: {str(e)}")
        sys.exit(1)

def parse_chromosome_region(region):
    if pd.isna(region) or not isinstance(region, str):
        return None, None, None

    match = re.match(r'(?:chr)?([\dXY]+):([\d.]+)-([\d.]+)', str(region))
    if match:
        chromosome = match.group(1)
        start = int(float(match.group(2).replace('.', '')))
        end = int(float(match.group(3).replace('.', '')))
        return chromosome, start, end

    logging.warning(f"Unable to parse region: {region}")
    return None, None, None

def preprocess_cnv_data(gs_df, nx_df, om_df):
    gs_df.rename(columns={'Chr': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)

    nx_df[['Chromosome', 'Start_Pos', 'End_Pos']] = nx_df['Chromosome Region'].apply(
        lambda x: pd.Series(parse_chromosome_region(x))
    )
    nx_df['Chromosome'] = pd.to_numeric(nx_df['Chromosome'], errors='ignore')

    om_df.rename(columns={'Chromosome': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)

    return gs_df, nx_df, om_df

def classify_cnv(cnv, gold_df):
    chrom, start, end = cnv['Chromosome'], cnv['Start_Pos'], cnv['End_Pos']
    if pd.isna(chrom) or pd.isna(start) or pd.isna(end):
        return "FP"

    for _, gold in gold_df.iterrows():
        if str(gold['Chromosome']) == str(chrom):
            overlap_start = max(start, gold['Start_Pos'])
            overlap_end = min(end, gold['End_Pos'])
            if overlap_start < overlap_end:
                overlap_length = overlap_end - overlap_start
                cnv_length = end - start
                if (overlap_length / cnv_length) >= 0.5:
                    return "TP"
    return "FP"

def classify_cnv_calls(df, gold_df):
    df['Class'] = df.apply(lambda row: classify_cnv(row, gold_df), axis=1)
    return df[df['Class'] == "TP"].drop(columns=['Class']), df[df['Class'] == "FP"].drop(columns=['Class'])

def find_false_negatives(gold_df, nx_df, om_df):
    detected_cnv = pd.concat([nx_df, om_df])
    fn_list = []

    for _, gold in gold_df.iterrows():
        chrom, start, end = gold['Chromosome'], gold['Start_Pos'], gold['End_Pos']
        overlap = detected_cnv[
            (detected_cnv['Chromosome'] == chrom) &
            (detected_cnv['Start_Pos'] <= end) &
            (detected_cnv['End_Pos'] >= start)
        ]

        if overlap.empty:
            fn_list.append(gold)

    return pd.DataFrame(fn_list)

def main(gs_file, nx_file, om_file, output_file):
    logging.info("\n" + "="*50)
    logging.info(f"Starting CNV comparison at: {datetime.now()}")
    logging.info("="*50)

    logging.info("\nLoading input files...")
    gs_df = load_cnv_data(gs_file)  # Now the Gold Standard
    nx_df = load_cnv_data(nx_file)
    om_df = load_cnv_data(om_file)

    logging.info("\nPreprocessing data...")
    gs_df, nx_df, om_df = preprocess_cnv_data(gs_df, nx_df, om_df)

    logging.info("\nClassifying CNVs...")
    tp_nx, fp_nx = classify_cnv_calls(nx_df, gs_df)  # Compare NxClinical against GenomStudio
    tp_om, fp_om = classify_cnv_calls(om_df, gs_df)  # Compare Ömer Software against GenomStudio

    logging.info("\nFinding False Negatives...")
    fn_nx = find_false_negatives(gs_df, nx_df, pd.DataFrame())  # False negatives for NxClinical
    fn_om = find_false_negatives(gs_df, pd.DataFrame(), om_df)  # False negatives for Ömer Software

    def calculate_metrics(tp, fp, fn):
        tp_count = len(tp)
        fp_count = len(fp)
        fn_count = len(fn)

        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        f1_score = (2 * recall * precision) / (recall + precision) if (recall + precision) > 0 else 0

        return recall, precision, f1_score

    nx_recall, nx_precision, nx_f1 = calculate_metrics(tp_nx, fp_nx, fn_nx)
    om_recall, om_precision, om_f1 = calculate_metrics(tp_om, fp_om, fn_om)

    logging.info("\nWriting results...")
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"### Analysis timestamp: {datetime.now()}\n\n")
        f.write(f"### Gold Standard (GenomStudio) ({len(gs_df)} adet):\n")
        f.write(format_cnv_output(gs_df, "GenomStudio", "Gold Standard"))

        f.write(f"\n### True Positive CNVs ({len(tp_nx) + len(tp_om)} adet):\n")
        f.write(format_cnv_output(tp_nx, "NxClinical", "TP"))
        f.write(format_cnv_output(tp_om, "Ömer Software", "TP"))

        f.write(f"\n### False Positive CNVs ({len(fp_nx) + len(fp_om)} adet):\n")
        f.write(format_cnv_output(fp_nx, "NxClinical", "FP"))
        f.write(format_cnv_output(fp_om, "Ömer Software", "FP"))

        f.write(f"\n### False Negative CNVs:\n")
        f.write(f"NxClinical: {len(fn_nx)} adet\n")
        f.write(f"Ömer Software: {len(fn_om)} adet\n")

        f.write(f"\n### Performance Metrics:\n")
        f.write(f"NxClinical:\n")
        f.write(f"  Recall: {nx_recall:.4f}\n")
        f.write(f"  Precision: {nx_precision:.4f}\n")
        f.write(f"  F1-Score: {nx_f1:.4f}\n")
        f.write(f"Ömer Software:\n")
        f.write(f"  Recall: {om_recall:.4f}\n")
        f.write(f"  Precision: {om_precision:.4f}\n")
        f.write(f"  F1-Score: {om_f1:.4f}\n")

    logging.info(f"Results saved to: {output_file}")
    print(f"Karşılaştırma tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Kullanım: python cnv_comparator.py <GS_File> <NX_File> <OM_File> <Output_File>")
        sys.exit(1)

    gs_file, nx_file, om_file, output_file = sys.argv[1:]
    main(gs_file, nx_file, om_file, output_file)
