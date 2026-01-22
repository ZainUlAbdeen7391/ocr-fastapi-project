import json
import re
# from input_module import fix_rtl_text


def parse_gpt_json(text: str) -> dict:


    if not text:
        return {}

    text = re.sub(r"```json|```", "", text).strip()

    return json.loads(text)


# def apply_rtl_for_display(data: dict) -> dict:

#     display_data = {}

#     for key, value in data.items():
#         if isinstance(value, str):
#             display_data[key] = value
#         else:
#             display_data[key] = value

#     return display_data



        
