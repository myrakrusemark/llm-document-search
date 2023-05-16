import requests
from bs4 import BeautifulSoup
import sys
import openai
import re  # import regular expression module
import sys
from tqdm import tqdm
from threading import Thread
import itertools
import time
import json

max_length = 3000  # The maximum sequence length the model can handle
overlap = 0.2

model = 'gpt-4' #Great for following directions
cost_per_k_prompt_tokens = 0.002
cost_per_k_completion_tokens = 0.002
token_avg_char_length = 4

# Load API key from credentials.json
with open('credentials.json') as f:
    credentials = json.load(f)
    api_key = credentials['openai_api_key']

# Set the API key
openai.api_key = api_key

def get_webpage_content(url, animation):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all 'a' tags (which define hyperlinks)
    for a in soup.find_all('a', href=True):
        if a.text:
            # Replace link text with formatted string (link text)[URL]
            a.string = f"{a.text}[{a['href']}]"

    # Stop the loading animation
    animation.stop()
    return str(soup)

def split_content_into_sections(content):
    # Parse the content with Beautiful Soup
    soup = BeautifulSoup(content, "html.parser")

    # Extract plain text content
    full_text = soup.get_text(separator="\n")

    # Remove consecutive newline characters
    full_text = re.sub('\n+', '\n', full_text)

    # Split full_text into sections
    sections = []
    start = 0
    end = max_length

    # Estimate the number of iterations for tqdm progress bar
    iterations = int(len(full_text) / (max_length * (1 - overlap)) + 1)

    with tqdm(total=iterations, file=sys.stdout, desc="Splitting content", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        while start < len(full_text):
            sections.append(full_text[int(start):int(end)])
            start = end - (max_length * overlap)
            end = start + max_length
            pbar.update(1)

    return sections

class LoadingAnimation:
    def __init__(self):
        self.stop_loading = False

    def start(self):
        self.animation = Thread(target=self.animate)
        self.animation.start()

    def animate(self):
        for c in itertools.cycle(['.  ', '.. ', '...', '   ']):
            if self.stop_loading:
                break
            sys.stdout.write('\rLoading URL' + c)
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\rDone!        ')

    def stop(self):
        self.stop_loading = True
        self.animation.join()

def num_tokens_from_string(string: str, token_avg_char_length: int) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(string) / token_avg_char_length
    return num_tokens

# Loop to perform search
while True:
    # Example usage
    url = input("Enter the URL: ")


    # Retrieve webpage content and strip HTML tags
    animation = LoadingAnimation()
    animation.start()
    webpage_content = get_webpage_content(url, animation)


    sections = split_content_into_sections(webpage_content)

    joined_sections = '\n'.join(sections)
    num_tokens = num_tokens_from_string(joined_sections, token_avg_char_length)
    estimated_cost_prompt = (num_tokens / 1000) * cost_per_k_prompt_tokens
    estimated_cost_completion = (len(sections) / 1000) * cost_per_k_completion_tokens
    estimated_cost = estimated_cost_prompt + estimated_cost_completion
    print(f"Estimated cost: ${estimated_cost:.2f}")


    if len(sections) <= 0:
        print("FULL TEXT")

        print('\n'.join(sections))
        exit()
    else:
        # Perform search with a progress bar
        search_term = input("\nEnter a search term ('new' to browse a new page, 'exit' to quit): ")
        if search_term.lower() == "exit":
            break
        if search_term.lower() == "new":
            continue

        results = []
        cost = 0.00
        with tqdm(total=len(sections), file=sys.stdout, desc="Searching: "+search_term, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            for section in sections:
                prompt = f"{section}\n\n"
                prompt += "Answer 'Yes' or 'No'. Does the content above contain information relating to the following search term? If the information contains a mention but overall has no context, then answer 'No'.\n\n"
                prompt += f"Search Term: {search_term}"
                message = [{'role': 'user', 'content': prompt}]

                while True:
                    try:
                        response = openai.ChatCompletion.create(
                            model=model,
                            messages=message,
                            temperature=0.0,
                            stream=False,
                            request_timeout=5,
                        )

                        prompt_tokens_used = response.usage.prompt_tokens
                        completion_tokens_used = response.usage.completion_tokens
                        cost_update = float(float(prompt_tokens_used/1000) * cost_per_k_prompt_tokens + float(completion_tokens_used/1000) * cost_per_k_completion_tokens)
                        cost += cost_update
                        if "Yes" in response.choices[0].message.content:
                            print(f"\n\n-----Relevant Content-----\n\n")
                            print(section)
                        else:
                            sys.stdout.write(".")
                        break
                    except openai.error.Timeout as e:
                        print("Timeout error: ", e)
                pbar.update(1)

        print("\n")
        print("Results found: ", len(results))
        print("Total cost: $", cost)
