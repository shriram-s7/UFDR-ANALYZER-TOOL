import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()

# --- Configuration ---
NUM_CONTACTS = 50
NUM_MESSAGES = 500
NUM_CALLS = 200

# --- 1. Generate Contacts ---
print("Generating Contacts...")
contacts = []
for _ in range(NUM_CONTACTS):
    contacts.append({
        'Name': fake.name(),
        'PhoneNumber': fake.phone_number()
    })
df_contacts = pd.DataFrame(contacts)
# Add our key suspects to the contact list
suspects = [
    {'Name': "John 'Apex' Doe", 'PhoneNumber': fake.phone_number()},
    {'Name': "Sarah 'Crypto' Connor", 'PhoneNumber': fake.phone_number()},
    {'Name': "The Broker", 'PhoneNumber': fake.phone_number()}
]
df_contacts = pd.concat([df_contacts, pd.DataFrame(suspects)], ignore_index=True)
df_contacts.to_csv('contacts.csv', index=False)
print("✅ Contacts data generated.")

# --- 2. Generate Messages ---
print("Generating Messages...")
keywords = ["money", "transfer", "deal", "bitcoin", "wallet", "crypto", "package", "urgent"]
participants = df_contacts['Name'].tolist()
messages = []
start_date = datetime.now() - timedelta(days=30)

for _ in range(NUM_MESSAGES):
    sender = random.choice(participants)
    recipient = random.choice([p for p in participants if p != sender])
    timestamp = start_date + timedelta(seconds=random.randint(0, 30*24*3600))
    body = fake.sentence(nb_words=10)
    if random.random() < 0.2: # 20% of messages have a keyword
        body += f" about the {random.choice(keywords)}."
    messages.append({
        'Timestamp': timestamp,
        'Sender': sender,
        'Recipients': recipient,
        'Body': body
    })
df_messages = pd.DataFrame(messages)
# --- ADD THIS BLOCK TO PLANT THE "GOLDEN THREAD" MESSAGE ---
golden_thread_message = {
    'Timestamp': datetime.now() - timedelta(days=5),
    'Sender': "John 'Apex' Doe",
    'Recipients': "The Broker",
    'Body': "System check alpha go. Confirm the usual rooftop location. The package (connector type) is ready."
}
df_messages = pd.concat([df_messages, pd.DataFrame([golden_thread_message])], ignore_index=True)
# --- END OF BLOCK ---
df_messages.to_csv('messages.csv', index=False)
print("✅ Messages data generated.")

# --- 3. Generate Call Logs ---
print("Generating Call Logs...")
calls = []
for _ in range(NUM_CALLS):
    caller = random.choice(participants)
    receiver = random.choice([p for p in participants if p != caller])
    timestamp = start_date + timedelta(seconds=random.randint(0, 30*24*3600))
    duration = random.randint(10, 1800) # Duration in seconds
    calls.append({
        'Timestamp': timestamp,
        'Caller': caller,
        'Receiver': receiver,
        'Duration (s)': duration
    })
df_calls = pd.DataFrame(calls)
df_calls.to_csv('calls.csv', index=False)
print("✅ Call logs data generated.")

print("\n🚀 All mock data files (contacts.csv, messages.csv, calls.csv) have been created successfully!")