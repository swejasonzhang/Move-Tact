import json
import os
from openai import OpenAI

# Load the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

def retrieveInfo(json_data):
    """
    Processes JSON data to extract relevant video metrics using OpenAI's GPT-3.5-turbo.
    Splits the data into two parts to handle large inputs and combines the results.
    """
    def split_data(data):
        """
        Splits the JSON data into two parts for processing.
        Handles both dictionaries and lists.
        """
        if isinstance(data, dict):
            items = list(data.items())
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Unsupported JSON data format. Expected dict or list.")

        # Split the data into two equal parts
        mid = len(items) // 2
        return items[:mid], items[mid:]

    def truncate_data(data, max_tokens=15000):
        """
        Truncates the data to fit within the model's token limit.
        Assumes 1 token ≈ 4 characters.
        """
        data_str = json.dumps(data)
        max_length = max_tokens * 4  # Calculate max allowed characters
        if len(data_str) > max_length:
            data_str = data_str[:max_length]
            data = json.loads(data_str)
        return data

    def call_openai_api(data_part):
        """
        Calls the OpenAI API to process the data and extract relevant metrics.
        """
        prompt_template = """
        The following is a JSON representation of a video (YouTube, TikTok, or Instagram). Extract the most relevant metrics and return them in a clean, structured JSON format.

        Extract the following information:
        1. Likes: The number of likes on the video.
        2. Comments: The number of comments on the video.
        3. Views: The number of views the video has.
        4. Song Name: If available, the name of the song associated with the video.
        5. Artist: If the song name is available, include the artist's name.
        6. Shares: The number of times the video has been shared.
        7. Any other relevant video statistics: If there are additional key metrics such as shares, reposts, or engagement scores, include them as well.

        JSON Data: {json_data}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt_template.replace("{json_data}", json.dumps(data_part))}
                ],
                max_tokens=200,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    # Split the JSON data into two parts
    try:
        data_part_1, data_part_2 = split_data(json_data)
    except ValueError as e:
        print(f"Error splitting data: {e}")
        return None

    # Truncate each part to fit within the token limit
    data_part_1 = truncate_data(data_part_1)
    data_part_2 = truncate_data(data_part_2)

    # Get responses for both parts
    filtered_data_part_1 = call_openai_api(data_part_1)
    filtered_data_part_2 = call_openai_api(data_part_2)

    if not filtered_data_part_1 or not filtered_data_part_2:
        print("Error: One or both parts of the data could not be processed.")
        return None

    try:
        # Safely parse the responses into JSON
        result_part_1 = json.loads(filtered_data_part_1)
        result_part_2 = json.loads(filtered_data_part_2)

        # Combine the two parts of the results without overwriting keys
        combined_results = {**result_part_1, **result_part_2}

        return combined_results

    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response into JSON: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None