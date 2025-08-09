import os
import re
import shutil
import markdown
import pandas as pd
import csv


# ===============================
# CONFIGURATION
# ===============================
CARDS_FOLDER = "cards"
FLASHCARDS_CSV = "flashcards.csv"
FAILED_CSV = "failed.csv"
SORT_IDS_CSV = "sortIDs.csv"
AUDIO_FOLDER = "audio"
USED_AUDIO_FOLDER = "usedAudio"

REQUIRED_SECTIONS = ["Meaning", "Reading", "Part of Speech"]
CSV_HEADER = ["word", "meaning", "reading", "part_speech", "content", "audio", "sort_id", "tags"]


# ===============================
# PART 1 - GENERATE FLASHCARDS CSV
# ===============================
def generate_flashcards():
    """Parses card files into a flashcards CSV and logs failures."""
    with open(FLASHCARDS_CSV, "w", encoding="utf-8") as csv_file, \
         open(FAILED_CSV, "w", encoding="utf-8") as failed_file:
        
        csv_file.write("\t".join(CSV_HEADER) + "\n")

        for filename in os.listdir(CARDS_FOLDER):
            if not filename.endswith(".txt"):
                continue
            
            filepath = os.path.join(CARDS_FOLDER, filename)
            kanji = filename.replace(".txt", "")

            with open(filepath, "r", encoding="utf-8") as card_file:
                card_html = markdown.markdown(card_file.read())

            found_sections = []
            content = ""

            for line in card_html.splitlines():
                add_to_content = True
                for section in REQUIRED_SECTIONS:
                    section_name = f"<li><strong>{section}:</strong>"
                    if section_name in line:
                        found_sections.append(
                            line.replace(section_name, "").replace("</li>", "").strip()
                        )
                        add_to_content = False
                        break

                if "flashcard" in line:
                    continue
                elif add_to_content:
                    content += line

            if len(found_sections) != len(REQUIRED_SECTIONS):
                print(f"[WARN] {kanji} has missing parts")
                failed_file.write(kanji + "\n")
            else:
                print(f"[OK] {kanji}")
                csv_file.write(
                    f"{kanji}\t" + "\t".join(found_sections) + f"\t{content}\n"
                )


# ===============================
# PART 2 - SORT MERGE WITH sortIDs.csv
# ===============================
def sort_flashcards():
    """Sorts flashcards by sort_id from SORT_IDS_CSV."""
    try:
        ids_df = pd.read_csv(SORT_IDS_CSV, sep="\t", encoding='utf-8')
        df = pd.read_csv(FLASHCARDS_CSV, sep="\t", encoding='utf-8')
    except FileNotFoundError as e:
        print(f"[ERROR] Missing file: {e}")
        return

    # Drop existing sort_id if present
    df.drop(columns=['sort_id'], errors='ignore', inplace=True)

    # Remove duplicates from sort IDs
    ids_df.drop_duplicates(subset=['word'], keep='first', inplace=True)

    # Merge
    merged_df = pd.merge(df, ids_df[['word', 'sort_id']], on='word', how='left', validate="one_to_one")

    # Sort
    merged_df['sort_id'] = pd.to_numeric(merged_df['sort_id'], errors='coerce')
    merged_df.sort_values(by='sort_id', na_position='last', inplace=True)
    merged_df['sort_id'] = merged_df['sort_id'].astype('Int64')

    # Reorder columns to put sort_id second-to-last
    if 'sort_id' in merged_df.columns:
        cols = list(merged_df.columns)
        cols.remove('sort_id')
        cols.insert(len(cols) - 1, 'sort_id')
        merged_df = merged_df[cols]

    merged_df.to_csv(FLASHCARDS_CSV, index=False, encoding='utf-8', sep="\t", quoting=csv.QUOTE_NONE)
    print(f"[INFO] '{FLASHCARDS_CSV}' sorted successfully.")


# ===============================
# PART 3 - ADD AUDIO LINKS AND COPY USED FILES
# ===============================
def create_audio_index(audio_folder):
    """Return a dict mapping words to audio filenames."""
    index = {}
    for filename in os.listdir(audio_folder):
        parts = re.split(r'[._-]', filename)
        if not parts:
            continue
        word = parts[0].lower()
        if word not in index:
            index[word] = filename
    return index


def add_audio_to_flashcards():
    """Adds audio references to CSV and saves used audio files."""
    try:
        df = pd.read_csv(FLASHCARDS_CSV, sep="\t", encoding='utf-8')
    except Exception as e:
        print(f"[ERROR] Could not open {FLASHCARDS_CSV}: {e}")
        return

    audio_index = create_audio_index(AUDIO_FOLDER)
    os.makedirs(USED_AUDIO_FOLDER, exist_ok=True)

    for i, row in df.iterrows():
        word = row['word']
        if word in audio_index:
            filename = audio_index[word]
            df.at[i, 'audio'] = f"[sound:{filename}]"

            try:
                shutil.copy2(
                    os.path.join(AUDIO_FOLDER, filename),
                    os.path.join(USED_AUDIO_FOLDER, filename)
                )
            except FileNotFoundError:
                print(f"[WARN] Missing audio file for {word}")
        else:
            print(f"[INFO] No audio for {word}")

    df.to_csv(FLASHCARDS_CSV, index=False, encoding='utf-8', sep="\t", quoting=csv.QUOTE_NONE)
    print(f"[INFO] Updated {FLASHCARDS_CSV} with audio links.")


# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    generate_flashcards()
    sort_flashcards()
    add_audio_to_flashcards()