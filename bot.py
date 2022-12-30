import telebot
import os
import requests
import json

bot = telebot.TeleBot("5832142181:AAF0G4i9XOR1K_LpCXmoSxOkFVhROb6_V40")
expenses = {}
adminids = ['52070608','129281848']

with open('state.json', 'r') as openfile:
    # Reading from json file
    expenses = json.load(openfile)

# Helper function to save expenses
def save_expense(user_id, amount, description, receipt=None):
    str_id = str(user_id)
    if str_id not in expenses:
        expenses[str_id] = []
    expenses[str_id].append({
        'amount': amount,
        'description': description,
        'receipt': receipt
    })
    # Serializing json
    json_object = json.dumps(expenses, indent=4)
     
    # Writing to sample.json
    with open("state.json", "w") as outfile:
        outfile.write(json_object)

# Handle '/start' and '/help' commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Welcome to the expenses bot. You can use this bot to record your expenses claims along with uploading pictures of receipts. To add a new expense, use the /add command. To view all expenses, use the /view command.")

# Handle '/add' command
@bot.message_handler(commands=['add'])
def add_expense(message):
    bot.send_message(message.chat.id, "Please enter the amount of the expense (without $ sign):")
    bot.register_next_step_handler(message, process_amount_step)

# Process the amount entered by the user
def process_amount_step(message):
    if message.text == 'exit':
        bot.send_message(message.chat.id, "Process exited!")
        return
    try:
        # Try to convert the message text to a float
        amount = float(message.text)
        # If successful, ask for a description
        bot.send_message(message.chat.id, "Please enter a description for the expense:")
        bot.register_next_step_handler(message, process_description_step, amount=amount)
    except ValueError:
        # If the conversion fails, display an error message
        bot.send_message(message.chat.id, "Sorry, that is not a valid amount. Please try again.  Otherwise, type 'exit' to quit")
        bot.register_next_step_handler(message, process_amount_step)

# Process the description entered by the user
def process_description_step(message, amount):
    description = message.text
    # Ask the user if they have a receipt for the expense
    bot.send_message(message.chat.id, "Do you have a picture of the receipt for this expense? (Yes/No)")
    bot.register_next_step_handler(message, process_receipt_step, amount=amount, description=description)

# Process the receipt answer entered by the user
def process_receipt_step(message, amount, description):
    if message.text == 'exit':
        bot.send_message(message.chat.id, "Process exited!")
        return
    if message.text.lower() == "yes":
        # If the user has a receipt, ask them to send it
        bot.send_message(message.chat.id, "Please send the picture of the receipt, only 1 image can be uploaded at once:")
        bot.register_next_step_handler(message, process_receipt_upload_step, amount=amount, description=description)
    elif message.text.lower() == "no":
        # If the user doesn't have a receipt, save the expense without it
        save_expense(message.from_user.id, amount, description, receipt=None)
        bot.send_message(message.chat.id, "Expense added successfully!")
    else:
        # If the user's answer is not "Yes" or "No", display an error message
        bot.send_message(message.chat.id, "Sorry, I didn't understand your response. Please enter Yes or No. Otherwise, type 'exit' to quit")
        bot.register_next_step_handler(message, process_receipt_step, amount=amount, description=description)

# Process the receipt image uploaded by the user
def process_receipt_upload_step(message, amount, description):
    if message.text == 'exit':
        bot.send_message(message.chat.id, "Process exited!")
        return
    if message.photo:
        file_id = message.photo[-1].file_id
        file = bot.get_file(file_id)
        file_content = requests.get(f'https://api.telegram.org/file/bot5832142181:AAF0G4i9XOR1K_LpCXmoSxOkFVhROb6_V40/{file.file_path}').content
        with open(f'receipt_{message.from_user.id}_{file_id}.jpg', 'wb') as f:
            f.write(file_content)

        save_expense(message.from_user.id, amount, description, receipt=f'receipt_{message.from_user.id}_{file_id}.jpg')
        # Send a message to confirm that the receipt has been saved
        bot.send_message(message.chat.id, "Expense added successfully! Please double check your claim details!")
    else:
        # If the message is not a photo, display an error message
        bot.send_message(message.chat.id, "Sorry, that is not a valid receipt. Please try again. Otherwise, type 'exit' to quit")
        bot.register_next_step_handler(message, process_receipt_upload_step, amount=amount, description=description)

# Handle '/view' command
@bot.message_handler(commands=['view'])
def view_expenses(message):
    # Check if the user has any expenses

    if str(message.from_user.id) not in expenses:
        bot.send_message(message.chat.id, "You don't have any expenses yet.")
    else:
        # If the user has expenses, display them
        total_amount = 0
        text = "Here are your expenses:\n\n"
        index = 1
        for expense in expenses[str(message.from_user.id)]:
            text += f"ID: {message.from_user.id}-{index}\n"
            text += f"Amount: ${expense['amount']}\nDescription: {expense['description']}\n"
            if expense['receipt']:
                text += "Receipt: Yes\n"
            else:
                text += "Receipt: No\n"
            text += "\n"
            total_amount += expense['amount']
            index += 1
        text += f"Total amount: ${total_amount}"
        bot.send_message(message.chat.id, text)

# Handle '/viewall' command
@bot.message_handler(commands=['viewall'])
def view_all_expenses(message):
    # Check if the user has the necessary permissions
    if str(message.from_user.id) not in adminids:
        bot.send_message(message.chat.id, "Sorry, you don't have permission to use this command.")
        return
    # If the user has the necessary permissions, display all expenses
    text = "Here are all the expenses:\n\n"
    for user_id in expenses:
        user = bot.get_chat(user_id)
        text += "-------------------\n"
        text += f"User: {user.username}\n\n"
        total_amount = 0
        index = 1
        for expense in expenses[user_id]:
            text += f"ID: {user_id}-{index}\n"
            text += f"Amount: ${expense['amount']}\nDescription: {expense['description']}\n"
            if expense['receipt']:
                text += "Receipt: Yes\n"
            else:
                text += "Receipt: No\n"
            text += "\n"
            total_amount += expense['amount']
            index += 1
        text += f"Total amount: ${total_amount}\n\n"
    bot.send_message(message.chat.id, text)

# Handle '/getfullclaimdetails' command
@bot.message_handler(commands=['getfullclaimdetails'])
def get_full_claim_details(message):
    # Check if the user has the necessary permissions
    if str(message.from_user.id) not in adminids:
        bot.send_message(message.chat.id, "Sorry, you don't have permission to use this command.")
        return
    # If the user has the necessary permissions, display all expenses
    for user_id in expenses:
        user = bot.get_chat(user_id)
        text = f"User: {user.username}\n"
        total_amount = 0
        for expense in expenses[user_id]:
            caption = text
            caption += f"Amount: ${expense['amount']}\nDescription: {expense['description']}\n"
            total_amount += expense['amount']
            if expense['receipt']:
                with open(expense['receipt'], 'rb') as f:
                    file_content = f.read()
            
                # Send the image to the user
                bot.send_photo(message.chat.id, file_content, caption=caption)
            else:
                bot.send_message(message.chat.id, caption)
            
@bot.message_handler(commands=['getreceipt'])
def get_receipt(message):
    bot.send_message(message.chat.id, "Please enter the claim ID:")
    bot.register_next_step_handler(message, process_getreceipt_step)

def process_getreceipt_step(message):
    id = message.text
    if id[0] == '#':
        id = id[1:]
    arr = id.split('-')
    user_id = arr[0]
    claim_index = int(arr[1]) - 1
    claim = expenses[user_id][claim_index]
    if claim['receipt']:
        user = bot.get_chat(user_id)
        caption = f"User: {user.username}\n"
        caption += f"Amount: ${claim['amount']}\nDescription: {claim['description']}\n"
        with open(claim['receipt'], 'rb') as f:
            file_content = f.read()
    
        # Send the image to the user
        bot.send_photo(message.chat.id, file_content, caption=caption)
    else:
        bot.send_message(message.chat.id, "No receipt found")

@bot.message_handler(commands=['changereceipt'])
def change_receipt(message):
    bot.send_message(message.chat.id, "Please enter the claim ID:")
    bot.register_next_step_handler(message, process_changereceipt_step)

def process_changereceipt_step(message):
    id = message.text
    if id[0] == '#':
        id = id[1:]
    arr = id.split('-')
    user_id = arr[0]
    claim_index = int(arr[1]) - 1
    file_name = expenses[user_id][claim_index]['receipt']

    bot.send_message(message.chat.id, "Please send the picture of the receipt, only 1 image can be uploaded at once:")
    bot.register_next_step_handler(message, process_change_receipt_upload_step, file_name = file_name)

def process_change_receipt_upload_step(message, file_name):
    if message.text == 'exit':
        bot.send_message(message.chat.id, "Process exited!")
        return
    if message.photo:
        file_id = message.photo[-1].file_id
        file = bot.get_file(file_id)
        file_content = requests.get(f'https://api.telegram.org/file/bot5832142181:AAF0G4i9XOR1K_LpCXmoSxOkFVhROb6_V40/{file.file_path}').content
        with open(file_name, 'wb') as f:
            f.write(file_content)
        bot.send_message(message.chat.id, "Receipt updated!")
    else:
        bot.send_message(message.chat.id, "Sorry, that is not a valid receipt. Please try again. Otherwise, type 'exit' to quit")
        bot.register_next_step_handler(message, process_change_receipt_upload_step, file_name = file_name)


# Handle '/getreceipts' command
@bot.message_handler(commands=['getreceipts'])
def get_receipts(message):
    if str(message.from_user.id) not in adminids:
        bot.send_message(message.chat.id, "Sorry, you don't have permission to use this command.")
        return

    files = os.listdir()
    
    # Loop through the files
    for file in files:
        # Check if the file is an image
        if file.endswith('.jpg') or file.endswith('.png'):
            # Read the image file
            with open(file, 'rb') as f:
                file_content = f.read()
            
            # Send the image to the user
            bot.send_photo(message.chat.id, file_content)

# Run the bot
bot.infinity_polling()