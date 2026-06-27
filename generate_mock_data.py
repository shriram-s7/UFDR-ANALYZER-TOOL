# File: generate_mock_data.py

import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

# --- Configuration ---
OUTPUT_CSV_FILE = 'messages.csv'
NUM_MESSAGES = 500

# Initialize Faker
fake = Faker()

# Create a cast of characters for our demo
participants = [
    "John 'Apex' Doe",
    "Sarah 'Crypto' Connor",
    "Agent Miller",
    "Anonymous_77",
    "The Broker"
]

# Keywords for testing the AI search
keywords = [
    "money", "transfer", "deal", "bitcoin", "wallet address", "crypto",
    "send the funds", "meet up", "package secured", "payment received",
    "account details", "urgent", "be discreet"
]

# --- Generate the Data ---
messages = []
start_date = datetime.now() - timedelta(days=30)

print(f"Generating {NUM_MESSAGES} mock messages for your prototype...")

for _ in range(NUM_MESSAGES):
    sender = random.choice(participants)
    recipient_list = [p for p in participants if p != sender]
    recipient = random.choice(recipient_list)
    timestamp = start_date + timedelta(seconds=random.randint(0, 30*24*3600))

    # 20% of messages will contain a keyword to make the demo interesting
    if random.random() < 0.2:
        body = f"{fake.sentence(nb_words=8)} {random.choice(keywords)}."
    else:
        body = fake.sentence(nb_words=12)

    messages.append({
        'Timestamp': timestamp.isoformat(),
        'Conversation': f"Chat with {recipient}",
        'Sender': sender,
        'Recipients': recipient,
        'Body': body
    })

# --- Save the data to a CSV file ---
df = pd.DataFrame(messages)
df.sort_values(by='Timestamp', inplace=True)
df.to_csv(OUTPUT_CSV_FILE, index=False)

print(f"✅ Success! Your sample data file '{OUTPUT_CSV_FILE}' is ready.")
print("You can now run the main app.")