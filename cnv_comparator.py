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

def load_cnv_data(file_path):
    """
    Load CNV data from Excel or CSV files without initial column validation
    since preprocessing handles the column standardization.
    """
    try:
        logging.info(f"Loading file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Load based on file extension
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
            logging.info(f"File contents (first 3 rows):")
            logging.info(f"\n{df.head(3)}")
            logging.info(f"File timestamp: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
            
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
            logging.info(f"File contents (first 3 rows):")
            logging.info(f"\n{df.head(3)}")
            logging.info(f"File timestamp: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
            
        else:
            raise ValueError("Unsupported file format. Please use .xlsx or .csv")
            
        # Basic validation
        if df.empty:
            raise ValueError(f"File {file_path} is empty")
            
        logging.info(f"Successfully loaded {file_path} with shape: {df.shape}")
        logging.info(f"Columns found: {', '.join(df.columns)}")
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
    """Veri setlerini ortak formatta normalize eder ve gerekli sütunları oluşturur."""
    
    # GenomStudio (GS)
    gs_df.rename(columns={'Chr': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)
    
    # NxClinical (NX) - Chromosome Region sütunu işleniyor
    nx_df[['Chromosome', 'Start_Pos', 'End_Pos']] = nx_df['Chromosome Region'].apply(
        lambda x: pd.Series(parse_chromosome_region(x))
    )
    
    # Ömer Software (OM)
    om_df.rename(columns={'Chromosome': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)

    # GoldStandart
    gold_df.rename(columns={'Chr': 'Chromosome', 'Start': 'Start_Pos', 'End': 'End_Pos'}, inplace=True)

    return gs_df, nx_df, om_df, gold_df

def check_overlap(row, df, tolerance=50000):
    """Bir CNV'nin başka bir DataFrame içinde belirli bir toleransla eşleşip eşleşmediğini kontrol eder."""
    chrom, start, end = row['Chromosome'], row['Start_Pos'], row['End_Pos']
    
    overlap = df[
        (df['Chromosome'] == chrom) & 
        (((df['Start_Pos'] - tolerance) <= end) & ((df['End_Pos'] + tolerance) >= start))
    ]
    
    return not overlap.empty

def compare_cnv(gs_df, nx_df, om_df, gold_df):
    """CNV verilerini karşılaştırarak ortak ve farklı CNV'leri belirler."""
    
    # Ortak CNV'leri belirle (toleranslı eşleşme)
    common_gs = gs_df[gs_df.apply(lambda row: check_overlap(row, nx_df) and check_overlap(row, om_df) and check_overlap(row, gold_df), axis=1)]
    common_nx = nx_df[nx_df.apply(lambda row: check_overlap(row, gs_df) and check_overlap(row, om_df) and check_overlap(row, gold_df), axis=1)]
    common_om = om_df[om_df.apply(lambda row: check_overlap(row, gs_df) and check_overlap(row, nx_df) and check_overlap(row, gold_df), axis=1)]
    common_gold = gold_df[gold_df.apply(lambda row: check_overlap(row, gs_df) and check_overlap(row, nx_df) and check_overlap(row, om_df), axis=1)]
    
    common_cnv = pd.concat([common_gs, common_nx, common_om, common_gold]).drop_duplicates()
    
    # Sadece bir veri setinde bulunan CNV'leri belirle
    unique_gs = gs_df[~gs_df.apply(lambda row: check_overlap(row, nx_df) or check_overlap(row, om_df) or check_overlap(row, gold_df), axis=1)]
    unique_nx = nx_df[~nx_df.apply(lambda row: check_overlap(row, gs_df) or check_overlap(row, om_df) or check_overlap(row, gold_df), axis=1)]
    unique_om = om_df[~om_df.apply(lambda row: check_overlap(row, gs_df) or check_overlap(row, nx_df) or check_overlap(row, gold_df), axis=1)]
    unique_gold = gold_df[~gold_df.apply(lambda row: check_overlap(row, gs_df) or check_overlap(row, nx_df) or check_overlap(row, om_df), axis=1)]

    return common_cnv, unique_gs, unique_nx, unique_om, unique_gold


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
    
    logging.info("\nComparing CNVs...")
    common_cnv, unique_gs, unique_nx, unique_om, unique_gold = compare_cnv(gs_df, nx_df, om_df, gold_df)
    
    logging.info("\nWriting results...")
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"### Analysis timestamp: {datetime.now()}\n\n")
        f.write(f"### Ortak CNV'ler ({len(common_cnv)} adet):\n")
        f.write(common_cnv.to_csv(index=False, sep='\t'))
        f.write(f"\n\n### Sadece GenomStudio'da Bulunan CNV'ler ({len(unique_gs)} adet):\n")
        f.write(unique_gs.to_csv(index=False, sep='\t'))
        f.write(f"\n\n### Sadece NxClinical'de Bulunan CNV'ler ({len(unique_nx)} adet):\n")
        f.write(unique_nx.to_csv(index=False, sep='\t'))
        f.write(f"\n\n### Sadece Ömer Software'de Bulunan CNV'ler ({len(unique_om)} adet):\n")
        f.write(unique_om.to_csv(index=False, sep='\t'))
        f.write(f"\n\n### Sadece Gold Standart'da Bulunan CNV'ler ({len(unique_gold)} adet):\n")
        f.write(unique_gold.to_csv(index=False, sep='\t'))
    
    logging.info("\nResults Summary:")
    logging.info(f"- Common CNVs: {len(common_cnv)}")
    logging.info(f"- Unique to GS: {len(unique_gs)}")
    logging.info(f"- Unique to NX: {len(unique_nx)}")
    logging.info(f"- Unique to OM: {len(unique_om)}")
    logging.info(f"- Unique to GOLD: {len(unique_gold)}")
    logging.info(f"\nResults saved to: {output_file}")
    logging.info("Analysis completed!")

    print(f"Karşılaştırma tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Kullanım: python cnv_comparator.py <GS_File> <NX_File> <OM_File> <Gold_File> <Output_File>")
        sys.exit(1)
    
    gs_file, nx_file, om_file, gold_file, output_file = sys.argv[1:]
    main(gs_file, nx_file, om_file, gold_file, output_file)