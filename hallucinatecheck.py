import markdown
import os
import re

# Regex to remove pronunciation guides like [kanji]
CLEAN_PATTERN = re.compile(r"\[.*?\]")
# Regex to find one or more Hiragana characters inside markdown bold
BOLD_HIRAGANA_PATTERN = re.compile(r"\*\*[\u3040-\u309F]+\*\*")
# Regex to check if a string is ONLY hiragana
ALL_HIRAGANA_PATTERN = re.compile(r"^[\u3040-\u309F]+$")
# Regex to find all hiragana within square brackets
BRACKET_HIRAGANA_PATTERN = re.compile(r"\[([\u3040-\u309F]+)\]")


def clean_japanese(text: str) -> str:
    """Removes patterns like [pronunciation] from the text."""
    return CLEAN_PATTERN.sub("", text)


def is_all_hiragana(text: str) -> bool:
    """Checks if the entire string consists of only hiragana characters."""
    return bool(ALL_HIRAGANA_PATTERN.fullmatch(text))


def extract_reading_section(raw_content: str) -> str:
    """Finds the '### Reading' section and returns the hiragana on the next line."""
    in_reading_section = False
    for line in raw_content.splitlines():
        if line.strip() == "### Reading":
            in_reading_section = True
            continue
        if in_reading_section and line.strip():
            return line.strip()
        elif in_reading_section and line.strip().startswith("###"):
            break
    return ""


def extract_bracketed_hiragana(raw_content: str) -> str:
    """Finds all hiragana within brackets (furigana) and joins them."""
    hiragana_parts = BRACKET_HIRAGANA_PATTERN.findall(raw_content)
    return "".join(hiragana_parts)


def check_kanji_breakdown_for_bold_hiragana(raw_content: str) -> bool:
    """Checks for bolded hiragana ONLY within the '### Kanji Breakdown' section."""
    in_kanji_breakdown_section = False
    for line in raw_content.splitlines():
        if line.strip() == "### Kanji Breakdown":
            in_kanji_breakdown_section = True
            continue
        elif line.strip().startswith("### "):
            in_kanji_breakdown_section = False
        if in_kanji_breakdown_section and BOLD_HIRAGANA_PATTERN.search(line):
            return True
    return False


def fix_bold_hiragana_in_kanji_breakdown(raw_content: str) -> str:
    """Removes lines with bolded hiragana from the '### Kanji Breakdown' section."""
    fixed_lines = []
    in_kanji_breakdown_section = False
    for line in raw_content.splitlines():
        if line.strip() == "### Kanji Breakdown":
            in_kanji_breakdown_section = True
        elif line.strip().startswith("### "):
            in_kanji_breakdown_section = False
        if in_kanji_breakdown_section and BOLD_HIRAGANA_PATTERN.search(line):
            continue
        fixed_lines.append(line)
    return "\n".join(fixed_lines)


# --- NEW FUNCTION ---
def remove_empty_antonyms_section(raw_content: str) -> str:
    """
    Finds the '### Antonyms' section. If its content contains 'none' (case-insensitive),
    removes the entire section (header and content).
    """
    lines = raw_content.splitlines()

    # Find the start and end of the Antonyms section, if it's "empty"
    antonyms_start_index = -1
    antonyms_end_index = -1

    for i, line in enumerate(lines):
        if line.strip() == "### Antonyms":
            # Check the next line to see if it's a "none" line
            if i + 1 < len(lines) and "none" in lines[i + 1].lower():
                antonyms_start_index = i
                # Now find where this section ends
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("### "):
                        antonyms_end_index = j
                        break
                # If no other header is found, it goes to the end of the file
                if antonyms_end_index == -1:
                    antonyms_end_index = len(lines)
                break  # Found what we're looking for, exit the outer loop

    # If we found a section to remove, build the new content
    if antonyms_start_index != -1:
        # Slicing creates the new list of lines without the target section
        new_lines = lines[:antonyms_start_index] + lines[antonyms_end_index:]
        # Join, remove trailing whitespace that might result, and add a final newline
        return "\n".join(new_lines).rstrip() + "\n"

    # Otherwise, return the original content unchanged
    return raw_content


# --- Main script ---

hallucination = open("hallucination.csv", "w", encoding="utf-8")
logged_card_count = 0
fixed_bold_hiragana_count = 0
fixed_antonyms_count = 0

for file in os.listdir("cards"):
    if "~" in file or "〜" in file:
        continue

    with open("cards/" + file, "r+", encoding="utf-8") as card:
        raw_cardcontent = card.read()

        # --- Evaluate all error conditions based on the ORIGINAL content ---
        word = file[:-4]
        cleaned_cardcontent = clean_japanese(raw_cardcontent).replace(" ", "")

        has_bad_bold_hiragana = not is_all_hiragana(
            word
        ) and check_kanji_breakdown_for_bold_hiragana(raw_cardcontent)

        is_missing_filename = word not in cleaned_cardcontent
        if is_missing_filename:
            official_reading = extract_reading_section(raw_cardcontent)
            if official_reading:
                furigana_string = extract_bracketed_hiragana(raw_cardcontent)
                is_rescued_by_furigana = official_reading in furigana_string
                is_rescued_by_reading_in_text = official_reading in cleaned_cardcontent
                if is_rescued_by_furigana or is_rescued_by_reading_in_text:
                    is_missing_filename = False

        has_double_bold = "****" in cleaned_cardcontent
        has_double_grave_accent = "``" in raw_cardcontent
        has_double_brackets = "[[" in raw_cardcontent or "]]" in raw_cardcontent

        # More specific check for the Antonyms section
        has_empty_antonyms = "### Antonyms" in raw_cardcontent and (
            "(none" in raw_cardcontent
            or "None (" in raw_cardcontent
            or "(N" in raw_cardcontent
        )

        # ACTION 1: LOGGING
        if (
            has_bad_bold_hiragana
            or is_missing_filename
            or has_double_bold
            or has_empty_antonyms
            or has_double_grave_accent
            or has_double_brackets
        ):

            if has_bad_bold_hiragana:
                print(f"has_bad_bold_hiragana: {word}")
            if is_missing_filename:
                print(f"is_missing_filename: {word}")
            if has_double_bold:
                print(f"has_double_bold: {word}")
            if has_empty_antonyms:
                print(f"has_empty_antonyms: {word}")
            if has_double_grave_accent:
                print(f"has_double_grave_accent: {word}")
            if has_double_brackets:
                print(f"has_double_brackets: {word}")

            logged_card_count += 1
            hallucination.write(word + "\n")

        # ACTION 2: FIXING (can apply multiple fixes to one card)
        content_after_fixes = raw_cardcontent
        made_a_fix = False

        # Fix 1: Remove empty Antonyms section
        new_content = remove_empty_antonyms_section(content_after_fixes)
        if new_content != content_after_fixes:
            print(f"Fixing empty Antonyms section for: {word}")
            fixed_antonyms_count += 1
            content_after_fixes = new_content
            made_a_fix = True

        # Fix 2: Remove bold hiragana from Kanji Breakdown
        if has_bad_bold_hiragana:
            print(f"Fixing bold hiragana in Kanji Breakdown for: {word}")
            fixed_bold_hiragana_count += 1
            content_after_fixes = fix_bold_hiragana_in_kanji_breakdown(
                content_after_fixes
            )
            made_a_fix = True

        # If any fixes were applied, write the updated content back to the file
        if made_a_fix:
            card.seek(0)
            card.write(content_after_fixes)
            card.truncate()


hallucination.close()
print(f"Process complete.")
print(f"Logged {logged_card_count} cards with one or more issues.")
print(
    f"Auto-fixed {fixed_bold_hiragana_count} cards with bolded hiragana in Kanji Breakdown."
)
print(f"Auto-fixed {fixed_antonyms_count} cards by removing empty Antonyms sections.")
