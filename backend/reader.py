# reader.py
# Assembles chart data and calls Claude API to generate the natal reading.

import anthropic
from prompts.system_prompt import SYSTEM_PROMPT

client = anthropic.Anthropic()


def get_reading(chart_data: dict) -> str:
    # TODO: format chart_data into a readable prompt
    user_message = f"Please give a reading for the following nativity:\n\n{chart_data}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
