# Rule Based AI Python ChatBot

import datetime
import time

name= input("Welcome, enter your name :")
presentHour= datetime.datetime.now().hour

if 5 <= presentHour <= 11:
    print("Good morning, ", name)
elif 11 <= presentHour <= 17:
    print("Good afternoon, ", name)
elif 17 <= presentHour <= 20:
    print("Good evening, ", name)
else:
    print("Good night, ", name)

    
print("Hello! Welcome to your ChatBot")
print("How can help you today")
print("You can ask me basic question, Type 'bye' to exit from the bot")

# Chatbot Momory Creation [ dictionary of responses ]
responses = {
    "hello": "Hi, welcome. How can I help you?",
    "how are you": "I am very fine. Thank you",
    "who are you": "I am smart AI chatbot",
    "motivate me": "Keep going. Every bug of your project makes you a better developer",
    "thank you": "Most welcome",
    "happy": "Great to hear that"
} 

# Method/function to get response of ChatBot
def getResponseOfBot(userQuestion):    
    userQuestion= userQuestion.lower()
    for eachKey in responses:
        if eachKey in userQuestion:
            return responses[eachKey]

    return "I am not able to tell that yet. I am still in learning mode"
    
# Take user input
while True:
    userInput= input("Please ask your question:")
    reply= getResponseOfBot(userInput)
    print("Bot response :", reply)

    if "bye" in userInput.lower():
        break