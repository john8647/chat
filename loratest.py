lora = {
    "Leah": "rosie_b",
    "Chloe": "chloe_f1",
    "Layla": "chloe_f0",
    "Alana": "Alana_f2"
}


character_name = "Alana"
age = "11"
description = "young girl"
lora_name = lora.get(character_name, "")
use_lora = bool(lora_name)

if use_lora:
    subject_line = f"{lora_name} age {age}  {description}"
else:
    subject_line = f"A real photo of {description}, age {age}."


print(subject_line)
