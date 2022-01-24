import boto3
import os
import json
import logging

log = logging.getLogger()
ARN_of_state_machine = os.environ["STATE_MACHINE_ARN"]
print(ARN_of_state_machine)
SSM_Document_name_windows = os.environ["SSM_DOCUMENT_WINDOWS"]
print(SSM_Document_name_windows)
SSM_Document_name_linux = os.environ["SSM_DOCUMENT_LINUX"]
print(SSM_Document_name_linux)


def lambda_handler(event, context):
    
    print(event)
    Message = event["Records"][0]["Sns"]["Message"]
    log.info(Message)
    tmp = json.loads(Message)
    Dimensions = tmp["Trigger"]["Dimensions"][1]

    Instance_ID = Dimensions.get("value")
    log.info(Instance_ID)
    executionArn = state(Instance_ID)
    log.info(f"State Machine {ARN_of_state_machine} triggered, {executionArn}")


def state(Instance_ID):

    sf = boto3.client("stepfunctions")
    input = '{"Instance_ID" : "%s", "SSM_Document_Name_Windows" : "%s", "SSM_Document_Name_Linux" : "%s"}' % (
        Instance_ID,
        SSM_Document_name_windows,
        SSM_Document_name_linux
    )  # "{\\\"Instance_ID\\\" : \\\"%s\\\"}" %Instance_ID
    print(input)
    response = sf.start_execution(stateMachineArn=ARN_of_state_machine, input=input)
    executionArn = response["executionArn"]
    return executionArn