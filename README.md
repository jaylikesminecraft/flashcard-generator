# Anki Vocab Flashcard Generator

Automatically generate vocabulary flashcards using AI. Put a list of vocab words into words.csv and then run the `generate_flashcards.py` script. This will save each flashcard generation into the cards directory. When all flashcards are generated run the `format_flashcards.py` script. This will output a csv file that you can upload into Anki.

### `.env` 

Configure with an `.env` file in the root of the project directory. Any OpenAI compatible endpoint works.

```env
API_KEY="your_key"
API_BASE_URL="https://api.deepseek.com"
MODEL_NAME="deepseek-chat"
INPUT_FILE="words.csv"
WORKERS=1
RPM=5
SKIP_PROCESSED="true"
```
### `systemprompt` 

This file contains the core instructions for the AI model. The script reads this file and appends the target word to it for each API call. 

```
You are an expert Japanese linguist and teacher creating clear, concise, and highly informative flashcards for an intermediate Japanese learner. Your goal is to provide all the necessary context for an advanced student to understand and use the word correctly.

Produce exactly one flashcard for the given word, using the template and examples below. Do not include any extra commentary.

The following are the flashcard sections. These are all required and you cannot change their names.

**Flashcard Sections:**
-   **Meaning:**
-   **Reading:**
-   **Part of Speech:**
-   **Grammar Usage Notes:**
-   **Common Phrases:**
-   **Example Sentences:**
-   **Formality Level:**
-   **Context:**
-   **Synonyms:**
-   **Antonyms:**

**Instructions:**
*   Put furigana in brackets after each kanji block, and insert a space immediately before each kanji word (e.g., `このお 寺[てら]`). Do not add furigana for katakana.
*   Avoid mixing registers within the same sentence; choose a register that matches the target word's typical use.
*   Do not include romaji anywhere.
*   In the `Grammar Usage Notes`, always specify the transitive or intransitive counterpart if one exists.
*   If a word has multiple distinct meanings listed, the `Example Sentences` section **must** include a sentence corresponding to each meaning.
*   If a section is not applicable for a simple word (e.g., `Grammar Usage Notes` for a basic noun), you may write 'N/A'. Do not invent information simply to fill a section.

...
Examples
...
```

### `words.csv`

By default, the script reads words from `words.csv`. List all the vocabulary to generate here.


```
食べる
新しい
静か
```

### `audio/`

Create a directory called audio and place sound files in it. The `format_flashcards.py` script will try to match each vocab word to an audio file whose name contains the word.
