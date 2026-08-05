def send_message(user_input):

    parts = user_input.lower().strip().split()

    # ⭐ IMAGE COMMAND INTERCEPT
    if len(parts) == 1 and parts[0] == "show":
        return "generate_image() function"


print(send_message("how"))