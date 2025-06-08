import os
from flask import current_app
from app.models import db, Folder, File
from sqlalchemy.dialects.postgresql import insert
import time

def bulk_insert_files(file_records, batch_size=5000):
    """
    file_records: list of dicts like [{'filename': 'file1', 'folder_id': 1}, ...]
    Inserts in batches with ON CONFLICT DO NOTHING.
    """
    for i in range(0, len(file_records), batch_size):
        batch = file_records[i:i+batch_size]
        stmt = insert(File).values(batch)
        # Avoid inserting duplicates (Postgres specific)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['filename', 'folder_id']
        )
        try:
            db.session.execute(stmt)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inserting batch: {e}")


def scan_and_insert_folders_and_files(app):
    root_path = os.getenv("EXTERNAL_MEDIA_ROOT")
    if not root_path or not os.path.isdir(root_path):
        app.logger.error("EXTERNAL_MEDIA_ROOT not set or invalid")
        return

    with app.app_context():
        current_app.logger.info("Starting folder and file scan...")

        # STEP 1: Discover all folder paths
        new_folders = []
        folder_paths = []  # list of (year, month, day, full_path)

        for year in sorted(os.listdir(root_path), reverse=True):
            if not year.isdigit():
                continue
            year_path = os.path.join(root_path, year)

            for month in sorted(os.listdir(year_path), reverse=True):
                if not month.isdigit():
                    continue
                month_path = os.path.join(year_path, month)

                for day in sorted(os.listdir(month_path), reverse=True):
                    if not day.isdigit():
                        continue
                    day_path = os.path.join(month_path, day)

                    if not os.path.isdir(day_path):
                        continue

                    year_i, month_i, day_i = int(year), int(month), int(day)
                    # Check if folder exists in DB
                    exists = Folder.query.filter_by(year=year_i, month=month_i, day=day_i).first()
                    if not exists:
                        new_folders.append(Folder(year=year_i, month=month_i, day=day_i))
                        folder_paths.append((year_i, month_i, day_i, day_path))

        # STEP 2: Bulk insert new folders
        if new_folders:
            db.session.bulk_save_objects(new_folders)
            db.session.commit()
            current_app.logger.info(f"Inserted {len(new_folders)} new folders.")

        # STEP 3: Build lookup map of (year, month, day) → folder.id
        folders = Folder.query.all()
        folder_map = {(f.year, f.month, f.day): f.id for f in folders}

        # STEP 4: Discover and insert new files
        file_records = []
        CHUNK_SIZE = 5000
        count_files = 0
        count_folders= 0
        start = time.time()

        for year, month, day, folder_path in folder_paths:
            count_folders = count_folders + 1
            folder_id = folder_map.get((year, month, day))
            folder_path = os.path.join(root_path, str(year), str(month).zfill(2), str(day).zfill(2))
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        count_files = count_files + 1
                        file_records.append({
                            'filename': entry.name,
                            'folder_id': folder_id
                        })
        
                    # ✅ Flush batch when chunk is full
                    if len(file_records) >= CHUNK_SIZE:
                        current_app.logger.info(f"Writing {len(file_records)} files to db")
                        count_files = count_files + len(file_records)
                        bulk_insert_files(file_records)
                        file_records.clear()  # 🧹 Clear memory

        end = time.time()

        current_app.logger.info(f"Read {count_folders} folders and {count_files} files indexing complete. It took {end - start:2f} seconds")

