const TelegramBot = require('node-telegram-bot-api');
const { NlpManager } = require('node-nlp');
const { Groq } = require("groq-sdk");

const token = '7214498731:AAEL7-noQEmg6ipYdIV7envcQhqL1h6W3jM'; // Replace with your own bot token
const bot = new TelegramBot(token, { polling: true });
const manager = new NlpManager({ languages: ['en'] });
const groq = new Groq({ apiKey: "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" });

const companyData = {
    "What does your company do?": "It's a community-based startup that guides the path for the all-round development of a college student.",
    "Where is your company located?": "Our company is headquartered in Jamshedpur, India.",
    "How can I contact your company?": "You can contact us via email at contact@eklipes.com or call us at (123) 456-7890.",
    "Who are you?": "We are Eklipes, a community-based startup.",
    "Who made you?": "Eklipes was founded by Ayush Kumar with the vision to support college students' development.",
    "Why did you start Eklipes?": "Eklipes was started to address the need for holistic development among college students, providing guidance and support in various aspects of their lives.",
    "What are your core values?": "At Eklipes, we value community, growth, and innovation, striving to create a positive impact on the lives of college students.",
    "What services do you offer?": "We offer personalized guidance programs, mentorship, workshops, and community events aimed at fostering personal and professional growth among college students.",
    "How can I get involved with Eklipes?": "You can join our community, participate in our events, or even apply to become a mentor. Visit our website or contact us for more information!"
};

// Train the NLP manager with the company data
for (const question in companyData) {
    manager.addDocument('en', question, question);
    manager.addAnswer('en', question, companyData[question]);
}

// Train and save the model
(async () => {
    await manager.train();
    manager.save();
})();

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const messageText = msg.text;
    const userName = msg.from.username;

    if (messageText === '/start') {
        bot.sendMessage(chatId, 'Welcome to the bot!');
        return;
    }

    const nlpResponse = await manager.process('en', messageText);

    if (nlpResponse.intent === 'None') {
        // If no intent found from NLP, fallback to GROQ
        try {
            const groqResponse = await getGroqChatCompletion(messageText);
            bot.sendMessage(chatId, groqResponse.choices[0]?.message?.content || 'I\'m sorry, I don\'t understand that question.');
            bot.sendMessage(2126096638, `*@${userName}:*
${messageText}

*Response:*
${groqResponse.choices[0]?.message?.content || 'I\'m sorry, I don\'t understand that question.'}`
            );
        } catch (error) {
            console.error('Error fetching GROQ response:', error);
            bot.sendMessage(chatId, 'I\'m sorry, I\'m unable to process your request right now.');
            bot.sendMessage(2126096638, `I\'m sorry, I\'m unable to process your request right now.`);
        }
    } else {
        // If intent found from NLP, send the NLP answer
        bot.sendMessage(chatId, nlpResponse.answer);
        bot.sendMessage(2126096638, `*@${userName}:*
${messageText}

*Response:*
${nlpResponse.answer}`
        );
    }
});

async function getGroqChatCompletion(userMessage) {
    return groq.chat.completions.create({
        messages: [
            {
                role: "user",
                content: userMessage,
            },
        ],
        model: "llama3-8b-8192",
    });
}
