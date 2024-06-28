import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
load_dotenv()

# Load the bot token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the Groq client
client = Groq(
    api_key=os.getenv('GROQ_API_KEY'),
)

# Initialize sentence transformer for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

# Company-specific data
company_data = {
    "What does your company do?": "It's a community-based startup that guides the path for the all-round development of a college student.",
    "Where is your company located?": "Our company is headquartered in Jamshedpur, India.",
    "How can I contact your company?": "You can contact us via email at contact@eklipes.com or call us at (123) 456-7890.",
    "Who are you?": "We are Eklipes, a community-based startup.",
    "Who made you?": "Eklipes was founded by Ayush Kumar with the vision to support college students' development.",
    "Why did you start Eklipes?": "Eklipes was started to address the need for holistic development among college students, providing guidance and support in various aspects of their lives.",
    "What are your core values?": "At Eklipes, we value community, growth, and innovation, striving to create a positive impact on the lives of college students.",
    "What services do you offer?": "We offer personalized guidance programs, mentorship, workshops, and community events aimed at fostering personal and professional growth among college students.",
    "How can I get involved with Eklipes?": "You can join our community, participate in our events, or even apply to become a mentor. Visit our website or contact us for more information!",
    # Add more company-specific FAQs here
}

# Encode company data
company_questions = list(company_data.keys())
company_embeddings = model.encode(company_questions, convert_to_tensor=True)


def generate_response(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Sorry, I couldn't generate a response at the moment. Please try again later."


# Function to handle user query
def handle_query(prompt):
    # Encode the prompt
    query_embedding = model.encode(prompt, convert_to_tensor=True)

    # Compute similarities
    similarities = util.pytorch_cos_sim(query_embedding, company_embeddings)

    # Find the most similar question
    best_match_idx = similarities.argmax()
    best_match_score = similarities[0][best_match_idx].item()

    # If the similarity is above a certain threshold, use the company data response
    threshold = 0.7  # Adjust this threshold based on your needs
    if best_match_score > threshold:
        response = company_data[company_questions[best_match_idx]]
    else:
        # Otherwise, generate a response using the AI model
        response = generate_response(prompt)

    return response


# Define the start function to handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your Eklipes bot. How can I help you today?')


# Define the echo function to handle messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    res = handle_query(update.message.text)
    await update.message.reply_text(res)
    message = (
            f"*@{update.message.from_user.username}:*\n" +
            f"{update.message.text}\n\n" +
            f"*Response:*\n" +
            f"{res}"
    )
    await context.bot.send_message(chat_id=2126096638, text=message)
    logger.info(f"user: {update.message.text}")
    logger.info(f"AI: {res}")
    print(update.message.chat_id)


# Main function to set up the bot
def main():
    # Create the Application object and pass in the bot's token
    application = ApplicationBuilder().token(TOKEN).build()

    # Register the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Register the message handler to echo back messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()
