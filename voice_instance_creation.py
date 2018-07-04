import boto3

instance_type = None
rigion_name = None

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Voice Instance Creation Service  " \
                    "Which type of instance you want to create ? "\
                    "Example : t2.micro, t2.small, t2.large "
    reprompt_text = "Please, Can you tell me  Which type of instance you want to create ? "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for coming to Voice Instance Creator " \
                    "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def create_instance_type_attributes(instance_type):
    return {"instanceType": instance_type}

def set_instance_type_in_session(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'TypeInstance' in intent['slots']:
        global instance_type
        instance_type = intent['slots']['TypeInstance']['value']
        session_attributes = create_instance_type_attributes(instance_type)
        speech_output = "Setting Instance Type as  " \
                        + instance_type + "."\
                        " In which region you want to deploy your instance ?"\
                        "Example : us-east-1, us-west-1"

        reprompt_text = "Can you tell me, In which region you want to deploy your instance ?" \
                        + instance_type + \
                        "."
    else:
        speech_output = "I'm not sure about this Instance Type " \
                        " Can you tell me, In which region you want to deploy your instance ?"

        reprompt_text = "Can you tell me, In which region you want to deploy your instance ? "

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def create_region_name_attributes(region_name):
    return {"regionName": region_name}


def set_region_name_in_session(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Region_Name' in intent['slots']:
        global region_name
        region_name = intent['slots']['Region_Name']['value']
        session_attributes = create_region_name_attributes(region_name)
        instancesIp = ec2_creator()

        if instancesIp == "Error":

            speech_output = "Thank you for providing all the information. " \
                            " Let me check  your Instance's Status. "\
    						" Meanwhile you can enjoy songs with Youtue."\
                            " Unfortunately, There is some error in creating EC2 Instance. "\
                            "Please retry after sometime."

            reprompt_text = "Hey, " \
                            " Let me check  your Instance's Status. "\
    						" Meanwhile you can enjoy songs with Youtue."\
                            " Unfortunately, There is some error in creating EC2 Instance. "\
                            "Please retry after sometime."

        else:

            speech_output = "Thank you for providing all the information. " \
                            " Let me check  your Instance's Status. "\
    						" Meanwhile you can enjoy songs with Youtue."\
                            " Congratulations, Your EC2 Instance has been created successfully. "\
                            "Your Instance IP is ." + instancesIp +" ."

            reprompt_text = "Hey, " \
                            " Congratulations, Your EC2 Instance has been created successfully. "\
                            "Your Instance IP is ." + instancesIp +" ."


    else:
        speech_output = "I'm not sure about this region name " \
                        "Can you tell me the region name again? "

        reprompt_text =  "Can you repeat the region name again? "

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- EC2 Instance Creator ------------------

def ec2_creator():
    ec2 = boto3.resource('ec2', region_name=rigion_name)
    instanceinfo = ec2.create_instances(
        ImageId='ami-9f086de0',
        MinCount=1,
        MaxCount=1,
        KeyName='LambdaEC2',
        SecurityGroupIds=[
            'default'
        ],
        InstanceType=instance_type
    )

    for instance in instanceinfo:
        ec2.create_tags(Resources=[instance.id],
        Tags=[
            {
                'Key': 'Name',
                'Value': 'EC2_From_lambda'
            },
        ])

    for instances in ec2.instances.all():
        instancesIp = instances.id

    if instanceinfo == 'null':
        return "Error"
    else:
        return instancesIp



# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "TypeIntent":
        return set_instance_type_in_session(intent, session)
    elif intent_name == "RegionIntent":
        return set_region_name_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
