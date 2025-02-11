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
    # Helper function to split the data
    def split_data(data):
        # Convert dictionary to a list of key-value pairs if it's a dictionary
        if isinstance(data, dict):
            data = list(data.items())
        elif isinstance(data, list):
            pass  # Assume it's already a list of items
        else:
            raise ValueError("Unsupported JSON data format. Expected dict or list.")

        # Now slice the list into two parts
        length = len(data)
        mid = length // 2
        return data[:mid], data[mid:]

    # Helper function to truncate data based on token limit
    def truncate_data(data, max_tokens=15000):
        """
        Truncates the data to fit within the model's token limit.
        Assumes 1 token ≈ 4 characters.
        """
        data_str = json.dumps(data)  # Convert data to a string
        max_length = max_tokens * 4  # Calculate max allowed characters
        if len(data_str) > max_length:
            data_str = data_str[:max_length]  # Truncate the string
            data = json.loads(data_str)  # Convert back to JSON
        return data

    # Define your prompt
    prompt_template = """
    The following is a JSON representation of a YouTube or TikTok video. The data is deeply nested under various keys and includes irrelevant information. Your task is to extract the most relevant metrics for a video post and return them in a clean, structured format as a JSON.

    Specifically, extract the following information:
    1. Likes: The number of likes on the video.
    2. Comments: The number of comments on the video.
    3. Views: The number of views the video has.
    4. Song Name: If available, the name of the song associated with the video.
    5. Artist: If the song name is available, include the artist's name.
    6. Shares: The number of times the video has been shared.
    7. Any other relevant video statistics: If there are additional key metrics such as shares, reposts, or engagement scores, include them as well.
    
    JSON Data: {json_data}
    """

    # Split the JSON data into two parts
    try:
        data_part_1, data_part_2 = split_data(json_data)
    except ValueError as e:
        print(f"Error splitting data: {e}")
        return None

    # Truncate each part to fit within the token limit
    data_part_1 = truncate_data(data_part_1)
    data_part_2 = truncate_data(data_part_2)

    # Function to call OpenAI API
    def call_openai_api(data_part):
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
