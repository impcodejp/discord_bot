import csv
from pathlib import Path

RECORD_CSV_PATH = r".data/ip_record.csv"

# クラス内での使用を想定
class CsvManager:
    def __init__(self):
        self.record_csv_path = Path(RECORD_CSV_PATH)
        self._initialize_file()

    def _initialize_file(self):
        """フォルダ作成とCSV初期化を安全に行う"""
        
        self.record_csv_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.record_csv_path.exists():
            try:
                with open(self.record_csv_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    header = ["日時", "現IPアドレス", "直近IPアドレス", "継続時間"]
                    writer.writerow(header)
                print(f"新規作成完了: {self.record_csv_path}")
                
            except PermissionError:
                print("エラー: ファイルへの書き込み権限がありません。")
        else:
            print(f"確認: {self.record_csv_path} は既に存在します。")

