"""
Synthetic email text dataset generator for phishing email classification.

Generates short "email body" texts labeled phishing (1) or legitimate (0).
Replace with a real corpus (e.g. Nazario phishing corpus + Enron ham emails)
for production training -- the training script (train_email_model.py)
works the same regardless of source, as long as the CSV has 'text' and
'label' columns.
"""

import random
import pandas as pd

random.seed(7)

PHISHING_TEMPLATES = [
    "Dear customer, your {service} account has been suspended. Click here to verify your identity within 24 hours: {link}",
    "URGENT: Unusual sign-in activity detected on your {service} account. Confirm your password now or your account will be locked: {link}",
    "Your {service} payment failed. Update your billing information immediately to avoid service interruption: {link}",
    "Congratulations! You have won a {prize}. Claim your reward now by entering your bank details here: {link}",
    "Security Alert: We noticed a login attempt from a new device. If this wasn't you, secure your account immediately: {link}",
    "Your invoice #{num} is overdue. Please make payment immediately to avoid legal action. Pay here: {link}",
    "Your {service} storage is full. Click below to upgrade or your files will be deleted in 48 hours: {link}",
    "Action required: Your tax refund of ${amount} is ready. Verify your details to receive your refund: {link}",
    "We could not process your recent {service} order. Please confirm your payment details to avoid cancellation: {link}",
    "Your password will expire today. Click here to reset it immediately and avoid losing access: {link}",
    "Final notice: Your {service} subscription will be cancelled. Renew now and confirm your card details: {link}",
    "IT Department: Your mailbox has exceeded its quota. Click here to validate your account or lose access: {link}",
]

LEGIT_TEMPLATES = [
    "Hi team, just a reminder that our weekly sync is moved to {time} tomorrow ({ref}). Let me know if that works for everyone.",
    "Thanks for your order #{num}! Your {service} package has shipped and should arrive within {days} business days.",
    "Hey, here's the report you asked for (ref: {ref}). Let me know if you have any questions or need changes before Friday.",
    "Reminder: your appointment with Dr. {name} is scheduled for {time} on {day}. Reply to confirm or reschedule.",
    "Hi, attaching the meeting notes from today's call (#{num}). Action items are highlighted at the bottom.",
    "Your monthly statement for {service} (account ending {ref}) is now available in your dashboard. No action is needed.",
    "Great catching up today! Looking forward to working together on the {project} project next quarter.",
    "Just a heads up, the office will be closed on {day} for the holiday. Have a great weekend!",
    "Here's the recipe you wanted (makes {days} servings) - hope you enjoy making it this weekend!",
    "Thanks for signing up for our newsletter. Here's a summary of this week's top {num} articles.",
    "Your subscription to {service} was renewed successfully (order #{num}). Thanks for being a loyal customer.",
    "Following up on our conversation about {project} - I've shared doc #{ref} with you, let me know your thoughts.",
    "Quick question - are you free for a {time} call on {day} to discuss the {project} roadmap?",
    "Lunch on {day} at {time}? Found a new place near the office, ref code {ref}.",
    "Your {service} order #{num} has been delivered. We hope you enjoy it!",
    "FYI - I've updated the {project} doc with the latest numbers (rev {ref}). Take a look when you can.",
]

SERVICES = ["Netflix", "PayPal", "Amazon", "Microsoft 365", "Apple ID", "Bank of America", "Spotify", "Dropbox", "Google", "Instagram"]
LINKS = ["http://bit.ly/3kXyZ1", "http://secure-verify-account.tk/login", "http://192.168.4.22/confirm",
         "https://account-update.xyz/verify", "http://paypal-alert.cf/secure"]
PRIZES = ["$1,000 Amazon Gift Card", "free iPhone 16", "$500 cash prize", "all-inclusive vacation"]
NAMES = ["Smith", "Lee", "Brown", "Garcia", "Patel"]
DAYS = ["Monday", "Wednesday", "Friday", "next Tuesday"]
TIMES = ["10:00 AM", "2:30 PM", "9:00 AM", "4:00 PM"]
PROJECTS = ["Phoenix", "Aurora", "Atlas", "Nimbus"]


def fill(template):
    return template.format(
        service=random.choice(SERVICES),
        link=random.choice(LINKS),
        prize=random.choice(PRIZES),
        num=random.randint(10000, 99999),
        amount=random.randint(200, 5000),
        time=random.choice(TIMES),
        day=random.choice(DAYS),
        days=random.randint(2, 7),
        name=random.choice(NAMES),
        project=random.choice(PROJECTS),
        ref=f"{random.randint(1000,9999)}",
    )


def generate_dataset(n_per_class=1000) -> pd.DataFrame:
    rows = []
    for _ in range(n_per_class):
        rows.append({"text": fill(random.choice(PHISHING_TEMPLATES)), "label": 1})
        rows.append({"text": fill(random.choice(LEGIT_TEMPLATES)), "label": 0})

    df = pd.DataFrame(rows).drop_duplicates(subset="text").reset_index(drop=True)
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(df.head(8))
    print(f"\nTotal samples: {len(df)}")
    print(df["label"].value_counts())
    df.to_csv("/home/claude/phishguard-ai/data/emails_dataset.csv", index=False)
    print("\nSaved to data/emails_dataset.csv")
