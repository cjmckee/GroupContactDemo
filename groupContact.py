global_map = {'cody': 5095555555,
                'trevor': 8642948274,
                'patrick': 7394231038,
                'isaiah': 2349872338,
                'alex': 3298743374 }

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, body):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard(title, body)
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)

def build_ssml_response(title, body):
    speechlet = {}
    speechlet['outputSpeech'] = build_SSMLSpeech(body)
    speechlet['card'] = build_SimpleCard(title, body)
    speechlet['shouldEndSession'] = True
    return build_response(speechlet)

def build_PlainSpeech(body):
    speech = {}
    speech['type'] = 'PlainText'
    speech['text'] = body
    return speech

def build_SSMLSpeech(body):
    speech = {}
    speech['type'] = 'SSML'
    speech['ssml'] = "<speak>" + body + "</speak>"
    return speech

def build_SimpleCard(title, body):
    card = {}
    card['type'] = 'Simple'
    card['title'] = title
    card['content'] = body
    return card

def build_response(message, session_attributes={}):
    response = {}
    response['version'] = '1.0'
    response['sessionAttributes'] = session_attributes
    response['response'] = message
    print response
    return response

def continue_dialog():
    message = {}
    message['shouldEndSession'] = False
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(message)

def build_response_cont(title, body, session_attributes):
    speechlet = {}
    speechlet['outputSpeech'] = build_PlainSpeech(body)
    speechlet['card'] = build_SimpleCard(title, body)
    speechlet['shouldEndSession'] = False
    return build_response(speechlet, session_attributes=session_attributes)

def spellDigitOutput(number):
    return "<say-as interpret-as=\"digits\">" + str(number) + "</say-as>"


# --------------- Functions that control the skill's behavior ------------------

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


def get_name(event, context):

    intent = event['request']['intent']
    session_attributes = event['session']

    user_name = intent['slots']['name']['value'].replace(' ', "").replace('.', "").lower()
    user_number = global_map.get(user_name)

    if user_number is not None:
        return build_ssml_response("find_name_intent", "The number is " + spellDigitOutput(user_number))
    else:
        return build_response_cont("find_name_intent", "Couldn't find it in the dictionary. Try again.", session_attributes)


def cancel_intent():
    return build_speechlet_response("Cancel", "You want to cancel")

def help_intent():
    return build_speechlet_response("Cancel", "You want help")

def stop_intent():
    return build_speechlet_response("Stop", "You want to stop")

# --------------- Events ------------------

def on_launch(event, context):

    session_attributes = {}

    return build_response_cont("Welcome", "Welcome to the Group Contact Demonstration!", session_attributes)


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


# --------------- Main handler ------------------

def lambda_handler(event, context):
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event, context)
    elif event['request']['type'] == "IntentRequest":
        return intent_router(event, context)
