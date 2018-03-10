# GroupContactDemo

This is a simple Alexa skill to get used to the code involved in handling simple Alexa requests in Lambda. This demo will be written in Python, but the logic is very similar if you were to write it in NodeJS. This skill lets you access phone numbers from Alexa.

Some things you're going to need for this demo:
* AWS Account
* [Amazon Developer Console](https://developer.amazon.com/)
* Echo device or [echosim.io](https://echosim.io/)

# Set up the Skill

So go to the developer console, go to Alexa -> Alexa Skills kit. Click on "Create Skill."
This is where you're going to name your skill. We're gonna use a custom model and then we hit Create Skill.

You get to choose an invocation for your skill, which is how Alexa knows to use your skill.

## Intents

What we're going to focus on are intents. Intents are how Alexa knows what you're asking her for and how we're going to hook information we give to Alexa through lambda. I'm going to have two intents. One is called `findByNameIntent` and the other is called `setInfoIntent`.

The first thing we're going to set up is the intent slot. This actually holds the information that we're giving Alexa. The one I will use is called `name` and the type is `AMAZON.SearchQuery` (which is the default for unstructured phrases). We put this slot into the intent so that Alexa knows what name we're using.

You get to set up some sample utterances for the intent, which is what you will say to Alexa to launch that intent. Some sample utterances for this might be "what is the contact information for {name}" or "how do I contact {name}." When you say these things, Alexa can fill in the blank and send that to your lambda function.

### Dialogue

`setInfoIntent` is going to have what is called a dialogue. A dialogue is when the user has a conversation with Alexa to give her the information she needs. For this intent, I'm going to give Alexa a name, and then she's going to ask me for a phone number. I'm going to add a slot called `name` with type `AMAZON.SearchQuery` and a slot called `number` with the type `AMAZON.PhoneNumber`. My utterances will all be something like "add contact for {name}." Notice that this doesn't include the number. Click on the slot for number to edit the dialogue. This slot should be required, and then I'm going to have Alexa prompt the user by saying "What is the phone number for this contact?" My response will be something like "The phone number is {number}" or just "{number}". We're gonna deal with this dialogue later in the lambda function.

There are also default intents that we can mess with called `AMAZON.CancelIntent`, `AMAZON.HelpIntent`, and `AMAZON.StopIntent`. We don't actually have to do anything here, but if you want custom behavior on cancels or stops, these are things you can target.

# Lambda Function

Lambda is an awesome feature from AWS that allows for serverless computing. Essentially, you put a piece of code here and then hook it up to a trigger (in our case, Alexa) and it will run whenever that event occurs. This incurs a lot less setup time and cost than setting up a server for such a simple script. The AWS Free Tier allows you to use 1 million Lambda requests per month!

We're gonna create a new function here and author from scratch. I've named my function `groupContact` and the runtime is Python 2.7. For the role, create one from a template and give it Simple Microservice permissions.

We're going to select Amazon Alexa as the trigger, and everything else will be default. 

Copy the ARN from the top right (starting with arn:aws:...) and go back to your skill and enter that as the endpoint. It should be item 4 on the skill builder checklist. You can now save and build the model for your skill.

## The Code

Since our function gets data about users and allows you to input them, it should really be part of a database so it can be updated realtime. In order to simplify the code and the demonstration, I just have a simple dictionary declared at the top of my function to pull data from. If you want to actually update and get real data, have your code pull from the DB instead of this map. :)

### lambda_handler

The main handler will deal with requests and direct them accordingly to either our `on_launch` function or our `intent_router`.
```
def lambda_handler(event, context):
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event, context)
    elif event['request']['type'] == "IntentRequest":
        return intent_router(event, context)
```

### helper functions

We're gonna need some helper functions to build responses. The `build_response` function will be our backbone and we will send our responses to Alexa in this way.

```
def build_response(message, session_attributes={}):
    response = {}
    response['version'] = '1.0'
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    print response 
    return response
```

All of the other helper functions will build some part of the response and then call this function to send a response to Alexa. I won't go into too much detail about these.

### on_launch

This function will be called when someone launches the skill with no particular intent. We want it to welcome the user and then keep the session going.
```
def on_launch(event, context):

    session_attributes = {}

    return build_response_cont("Welcome", "Welcome to the Group Contact Demonstration!", session_attributes)
```

### intent_router

This function is gonna pull the intent part of the request and then direct it to our intent functions. 
```
def intent_router(event, context):

    intent = event['request']['intent']['name']
    # Custom Intents
    if intent == "findByNameIntent":
        return get_name(event, context)
    if intent == "setInfoIntent":
        return set_info(event, context)
    # Required Intents
    if intent == "AMAZON.CancelIntent":
        return cancel_intent()
    if intent == "AMAZON.HelpIntent":
        return help_intent()
    if intent == "AMAZON.StopIntent":
        return stop_intent()
```

## Custom Intents

Now we have the code for our custom intents.

### get_name

This function is going to retrieve the value of the name that the user gives Alexa and then search the map for it. We replace all spaces and periods and then convert to lowercase. The reason we do this is because sometimes Alexa can't understand your name, and you can actually spell it for her. For instance, when I spell it, the name gets input as "c. o. d. y." so it gets cleaned up and inserted as "cody."

If the phone number is found in the dictionary, we build the response and have Alexa read the phone number. If not, we say we couldn't find it, but we keep the session alive so that the user can ask again.

```
def get_name(event, context):

    intent = event['request']['intent']
    session_attributes = event['session']

    user_name = intent['slots']['name']['value'].replace(' ', "").replace('.', "").lower()
    user_number = global_map.get(user_name)

    if user_number is not None:
        return build_ssml_response("find_name_intent", "The number is " + spellDigitOutput(user_number))
    else:
        return build_response_cont("find_name_intent", "Couldn't find it in the dictionary. Try again.", session_attributes)
```

### set_info

This is the function that contains the dialogue where Alexa is going to converse with the user. We deal with this differently. We take the dialog state so that we know where the user is in conversing with Alexa. If the dialog state is started or in-progress, that means that Alexa is eliciting information from the user and we just `continue_dialog()`. If dialog is completed, then Alexa has gotten all the information she needs, and we can add it to the dictionary. My dictionary doesn't actually persist, so if you want to keep this data, this is where you should set up the database. 

```
def set_info(event, context):

    dialog_state = event['request']['dialogState']
    intent = event['request']['intent']

    if dialog_state in ("STARTED", "IN_PROGRESS"):
        return continue_dialog()
    elif dialog_state == "COMPLETED":
        user_name = intent['slots']['name']['value'].replace(' ', "").replace('.', "").lower()
        user_number = intent['slots']['number']['value']
        global_map[user_name] = user_number
        return build_ssml_response("info_intent", str(user_name) + " added with number " + spellDigitOutput(user_number))
    else:
        return build_speechlet_response("info_intent", "No dialog")
```

So this is all we need to do. Copy my file from the github into the inline code of the lambda function and save it. We can now test our skill.

# Testing

You can go to [echosim.io](https://echosim.io/) to test your skill. You log in with your account and then you can use echosim just like you would an echo device. Use your invocation and then test out your sample utterances.

Hopefully this was helpful in figuring out what is going on behind the scenes. You should mess around with the event structure to figure out the specifics about how these requests are handled. 

You can launch your skill publicly from the developer console if you want to access it publicly. Otherwise, it will still always be available on any devices that you have logged into and activated the skill on.
