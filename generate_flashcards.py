import multiprocessing
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

def init_worker(api_key, base_url):
    global worker_client
    worker_client = OpenAI(api_key=api_key, base_url=base_url)

def create_flashcard(word, model_name):
    """
    Calls the API to generate flashcard content for a given word.
    """
    prompt_template = open("systemprompt", encoding="utf-8").read()
    prompt = f"{prompt_template}\n\n**{word}**"
    
    messages = [{"role": "user", "content": prompt}]
    response = worker_client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=8192,
        temperature=1.3,
    )
    return response.choices[0].message.content

def process_word(word, model_name, skip_processed, processed_words, last_call_time, lock, seconds_per_request):
    """
    Manages the processing for a single word.
    """
    word = word.strip()
    if not word:
        return

    if skip_processed and word in processed_words:
        print(f"Skipping word '{word}' as it already exists.")
        return

    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        try:
            # Rate limiting logic
            if seconds_per_request > 0:
                with lock:
                    elapsed = time.time() - last_call_time.value
                    if elapsed < seconds_per_request:
                        time.sleep(seconds_per_request - elapsed)
                    last_call_time.value = time.time()

            time1 = time.time()
            flashcard = create_flashcard(word, model_name)
            delta = time.time() - time1

            output_path = os.path.join("cards", f"{word}.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(flashcard)
            
            print(f"Card for '{word}' created in {delta:.1f}s.")
            return # Success

        except Exception as e:
            attempts += 1
            print(e)
            print(f"ERROR processing '{word}' (Attempt {attempts}/{max_attempts}). Retrying...")
            if attempts < max_attempts:
                time.sleep(5 * attempts) # Exponential backoff

    print(f"FAILED: Could not process '{word}' after {max_attempts} attempts.")

# --- Main Execution Block ---

def main():
    load_dotenv()

    # --- Load Configuration from .env file ---
    api_key = os.getenv("API_KEY")
    api_base_url = os.getenv("API_BASE_URL", None)
    model_name = os.getenv("MODEL_NAME")
    input_file = os.getenv("INPUT_FILE")
    num_workers = int(os.getenv("WORKERS", 1))
    rpm = int(os.getenv("RPM", 0))
    # Convert string "true" or "false" to boolean
    skip_processed = os.getenv("SKIP_PROCESSED", "true").lower() in ('true', '1', 't')

    if not api_key:
        print("CRITICAL: API_KEY not found in .env file or environment variables. Exiting.")
        exit(1)

    os.makedirs("cards", exist_ok=True)
    try:
        with open(input_file, encoding="utf-8") as words_file:
            words = [word.strip() for word in words_file if word.strip()]
    except FileNotFoundError:
        print(f"CRITICAL: Input file '{input_file}' not found. Exiting.")
        return

    processed_words = [f.replace(".txt", "") for f in os.listdir("cards")] if skip_processed else []
    seconds_per_request = 60.0 / rpm if rpm > 0 else 0
    rate_limit_display = f"{rpm} RPM ({seconds_per_request:.2f}s/req)" if rpm > 0 else "Unlimited"

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    last_call_time = manager.Value('d', time.time() - seconds_per_request)

    print("--- Configuration ---")
    print(f"  Endpoint URL:   {api_base_url}")
    print(f"  Model:          {model_name}")
    print(f"  Workers:        {num_workers}")
    print(f"  API Rate Limit: {rate_limit_display}")
    print(f"  Skip Processed: {skip_processed}")
    print("---------------------")
    print(f"Starting processing for {len(words)} words from '{input_file}'...")

    initargs = (api_key, api_base_url)
    with multiprocessing.Pool(processes=num_workers, initializer=init_worker, initargs=initargs) as pool:
        tasks = [(word, model_name, skip_processed, processed_words, last_call_time, lock, seconds_per_request) for word in words]
        pool.starmap(process_word, tasks)

    print("\nAll words have been processed.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()