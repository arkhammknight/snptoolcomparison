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

def format_cnv_output(df, software_name):
    """CNV listesini yazılım adına göre biçimlendirerek döndürür."""
    count = len(df)
    if df.empty:
        return f"\n### {software_name} (CNV bulunamadı)\n\n"

    output = f"\n### {software_name} ({count} adet TP CNV)\n"
    output += "Chromosome\tStart_Pos\tEnd_Pos\tLength\n"
    
    for _, row in df.iterrows():
        output += f"{row['Chromosome']}\t{row['Start_Pos']}\t{row['End_Pos']}\t{row.get('Length', '')}\n"
    
    return output

def load_cnv_data(file_path):
    """CNV verilerini yükler."""
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
    """NxClinical'deki 'Chromosome Region' sütununu parçalayarak kromozom, start ve end çıkarır."""
    match = re.match(r'chr(\d+):([\d.]+)-([\d.]+)', str(region))
    if match:
        chromosome = int(match.group(1))  # Kromozom numarası
        start = int(match.group(2).replace('.', ''))  # Noktalı sayıyı tam sayıya çevir
        end = int(match.group(3).replace('.', ''))  # Noktalı sayıyı tam sayıya çevir
        return chromosome, start, end
    return None, None, None

def preprocess_cnv_data(gs_df, nx_df, om_df, gold_df):
    """Veri setlerini ortak formatta normalize eder."""
    gs_df.rename(columns={'Chr': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)
    
    nx_df[['Chromosome', 'Start_Pos', 'End_Pos']] = nx_df['Chromosome Region'].apply(
        lambda x: pd.Series(parse_chromosome_region(x))
    )
    
    om_df.rename(columns={'Chromosome': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)
    gold_df.rename(columns={'Chr': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)
    
    return gs_df, nx_df, om_df, gold_df

def is_true_positive(cnv, gold_df):
    """Bir CNV'nin altın standart veri ile %50 veya daha fazla örtüşüp örtüşmediğini kontrol eder."""
    chrom, start, end = cnv['Chromosome'], cnv['Start_Pos'], cnv['End_Pos']
    
    for _, gold in gold_df.iterrows():
        if gold['Chromosome'] == chrom:
            overlap_start = max(start, gold['Start_Pos'])
            overlap_end = min(end, gold['End_Pos'])
            
            if overlap_start < overlap_end:  # Gerçek bir örtüşme varsa
                overlap_length = overlap_end - overlap_start
                cnv_length = end - start
                
                if (overlap_length / cnv_length) >= 0.5:  # %50'den fazla örtüşüyorsa
                    return True
    return False

def find_true_positives(df, gold_df):
    """Verilen yazılımın CNV çağrılarından true positive (TP) olanları belirler."""
    return df[df.apply(lambda row: is_true_positive(row, gold_df), axis=1)]

def main(gs_file, nx_file, om_file, gold_file, output_file):
    logging.info("\n" + "="*50)
    logging.info(f"Starting CNV comparison at: {datetime.now()}")
    logging.info("="*50)
    
    logging.info("\nLoading input files...")
    gs_df = load_cnv_data(gs_file)
    nx_df = load_cnv_data(nx_file)
    om_df = load_cnv_data(om_file)
    gold_df = load_cnv_data(gold_file)
    
    logging.info("\nPreprocessing data...")
    gs_df, nx_df, om_df, gold_df = preprocess_cnv_data(gs_df, nx_df, om_df, gold_df)
    
    logging.info("\nFinding true positive CNVs...")
    tp_gs = find_true_positives(gs_df, gold_df)
    tp_nx = find_true_positives(nx_df, gold_df)
    tp_om = find_true_positives(om_df, gold_df)
    
    logging.info("\nWriting results...")
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"### Analysis timestamp: {datetime.now()}\n\n")
        f.write(f"### True Positive CNVs ({len(tp_gs) + len(tp_nx) + len(tp_om)} adet):\n")
        
        f.write(format_cnv_output(tp_gs, "GenomStudio"))
        f.write(format_cnv_output(tp_nx, "NxClinical"))
        f.write(format_cnv_output(tp_om, "Ömer Software"))
    
    logging.info(f"Results saved to: {output_file}")
    print(f"Karşılaştırma tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Kullanım: python cnv_comparator.py <GS_File> <NX_File> <OM_File> <Gold_File> <Output_File>")
        sys.exit(1)
    
    gs_file, nx_file, om_file, gold_file, output_file = sys.argv[1:]
    main(gs_file, nx_file, om_file, gold_file, output_file)