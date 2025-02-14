import pandas as pd
import sys

def load_cnv_data(file_path):
    """Excel dosyasını yükleyerek CNV verilerini içeren bir DataFrame döndürür."""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Hata: {file_path} yüklenirken sorun oluştu - {e}")
        sys.exit(1)

def compare_cnv(gs_df, nx_df, om_df):
    """CNV verilerini karşılaştırarak ortak ve farklı CNV'leri belirler."""
    common_cnv = gs_df.merge(nx_df, on='CNV_ID', how='inner').merge(om_df, on='CNV_ID', how='inner')
    unique_gs = gs_df[~gs_df['CNV_ID'].isin(nx_df['CNV_ID']) & ~gs_df['CNV_ID'].isin(om_df['CNV_ID'])]
    unique_nx = nx_df[~nx_df['CNV_ID'].isin(gs_df['CNV_ID']) & ~nx_df['CNV_ID'].isin(om_df['CNV_ID'])]
    unique_om = om_df[~om_df['CNV_ID'].isin(gs_df['CNV_ID']) & ~om_df['CNV_ID'].isin(nx_df['CNV_ID'])]
    
    return common_cnv, unique_gs, unique_nx, unique_om

def main(gs_file, nx_file, om_file, output_file):
    gs_df = load_cnv_data(gs_file)
    nx_df = load_cnv_data(nx_file)
    om_df = load_cnv_data(om_file)
    
    common_cnv, unique_gs, unique_nx, unique_om = compare_cnv(gs_df, nx_df, om_df)
    
    with open(output_file, 'w') as f:
        f.write("### Ortak CNV'ler:\n")
        f.write(common_cnv.to_csv(index=False, sep='\t'))
        f.write("\n\n### Sadece GenomStudio'da Bulunan CNV'ler:\n")
        f.write(unique_gs.to_csv(index=False, sep='\t'))
        f.write("\n\n### Sadece NxClinical'de Bulunan CNV'ler:\n")
        f.write(unique_nx.to_csv(index=False, sep='\t'))
        f.write("\n\n### Sadece Ömer Software'de Bulunan CNV'ler:\n")
        f.write(unique_om.to_csv(index=False, sep='\t'))
    
    print(f"Karşılaştırma tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Kullanım: python cnv_comparator.py <GS_File> <NX_File> <OM_File> <Output_File>")
        sys.exit(1)
    
    gs_file, nx_file, om_file, output_file = sys.argv[1:]
    main(gs_file, nx_file, om_file, output_file)
