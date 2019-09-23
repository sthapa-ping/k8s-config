import json
import logging
import signal
import time
from urllib2 import build_opener, HTTPHandler, Request
from github import Github

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def lambda_handler(event, context):
    #'''Handle Lambda event from AWS'''
    ## Setup alarm for remaining runtime minus a second
    #signal.alarm((context.get_remaining_time_in_millis() / 1000) - 1)
    try:
        LOGGER.info('REQUEST RECEIVED:\n %s', event)
        LOGGER.info('REQUEST RECEIVED:\n %s', context)
 
        # Set github variables from event
        ghToken = event['ResourceProperties']['GitHubToken']
        repoName = event['ResourceProperties']['RepoName']
        repoDesc = event['ResourceProperties']['RepoDescription']
        deleteRepo = event['ResourceProperties']['DeleteRepo']
        g = Github(event['ResourceProperties']['GitHubToken'])
        user = g.get_user()

        if event['RequestType'] == 'Create':
            LOGGER.info('CREATE!')
            user.create_repo(
                event['ResourceProperties']['RepoName'],
                allow_rebase_merge=True,
                auto_init=False,
                description=event['ResourceProperties']['RepoDescription'],
                has_issues=True,
                has_projects=False,
                has_wiki=False,
                private=False,
            )
            send_response(event, context, "SUCCESS",
                          {"Message": "Resource creation successful!"})
        elif event['RequestType'] == 'Update':
            LOGGER.info('UPDATE!')
            send_response(event, context, "SUCCESS",
                          {"Message": "Resource update successful!"})
        elif event['RequestType'] == 'Delete':
            LOGGER.info('DELETE!')
            if deleteRepo == 'true':
                repo = user.get_repo(event['ResourceProperties']['RepoName'])
                repo.delete()
            else:
                LOGGER.info('deleteRepo set to false.  Not deleting')

            send_response(event, context, "SUCCESS",
                          {"Message": "Resource deletion successful!"})
        else:
            LOGGER.info('FAILED!')
            send_response(event, context, "FAILED",
                          {"Message": "Unexpected event received from CloudFormation"})
    except Exception as e: 
        LOGGER.info('FAILED!')
        LOGGER.info('EXCEPTION:\n %s', e)

        send_response(event, context, "FAILED", {
            "Message": "Exception during processing"})

def send_response(event, context, response_status, response_data):
    '''Send a resource manipulation status response to CloudFormation'''
    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })

    LOGGER.info('ResponseURL: %s', event['ResponseURL'])
    LOGGER.info('ResponseBody: %s', response_body)

    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=response_body)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    LOGGER.info("Status code: %s", response.getcode())
    LOGGER.info("Status message: %s", response.msg)


#def timeout_handler(_signal, _frame):
#    '''Handle SIGALRM'''
#    raise Exception('Time exceeded')
#
#
#signal.signal(signal.SIGALRM, timeout_handler)
