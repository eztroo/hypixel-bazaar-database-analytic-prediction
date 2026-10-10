import pandas as pd

df_bazaar = pd.read_parquet("backup/2026-09-19/bazaar_snapshots.parquet")
df_mayor = pd.read_parquet("backup/2026-09-19/mayor_snapshots.parquet")

print(f"Shape bazaar_snapshots.parquet : {df_bazaar}")          # (jumlah baris, jumlah kolom)
print(f"Shape mayor_snapshots.parquet : {df_mayor}")