import boto3
import os
from botocore.vendored import requests
import json
import traceback
import urllib3


webhook_url = os.environ['SLACK_WEBHOOK_URL']
defaultRegion = os.environ['REGION']
vpcId = os.environ['VPC_ID']

## Lambda python function to check available IP count in Subnet
def lambda_handler(event, context):
    try:
        ec2 = boto3.resource('ec2')
        client = boto3.client('ec2', region_name=defaultRegion)

        ### Get Subnets related vpc

        response = client.describe_subnets(
            Filters=[
                {
                    'Name':'tag:Name',
                    'Values':['*'],
                },
                {
                    'Name':'vpc-id',
                    'Values':[vpcId],
                }
            ]
        )


        ### Describe VPC from vpcid

        responseVpc = client.describe_vpcs(
            Filters=[
                {
                  'Name':'tag:Name',
                  'Values':['*'],
                },
                {
                  'Name':'vpc-id',
                  'Values':[vpcId], 
                }
            ]
        )

        vpcName = responseVpc['Vpcs'][0]['Tags'][0]['Value']


        ## Check availableipaddresscount 
        def slack_notification(message):
            slack_data = {
                'text': message,
                'blocks': [
                  {
                    "type": "divider"
                  },
                  {
                    "type": "header",
                    "text": {
                      "type": "plain_text",
                      "text": ":red_circle: Number of Available IPv4 at critical level "
                    }
                  },
                  {
                    "type": "section",
                    "block_id": "section567",
                    "text": {
                      "type": "mrkdwn",
                      "text": message
                    }
                  },
                  {
                    "type": "section",
                    "text": {
                      "type": "mrkdwn",
                      "text": "*Related VPC Name:* " + vpcName + " (" + vpcId + ")"
                    }
                  },
                  {
                    "type": "divider"
                  }
                ]
            }
            response = requests.post(
                webhook_url, data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
                )
            
        def get_subnet_tag_name(subnetid):
            subnetName = client.describe_subnets(
              Filters=[
                  {
                      'Name':'subnet-id',
                      'Values':[subnetid],
                  },
              ]
          )
            return subnetName['Subnets'][0]['Tags'][0]['Value']    

        for subnet in response['Subnets']:
              if subnet['AvailableIpAddressCount'] < 500:

                checkedSubnet = get_subnet_tag_name(subnet['SubnetId'])

                print("Subnet: *{0}* ".format(checkedSubnet) + subnet['SubnetId'] + " has not enough available IPs" + ", " + "It has " + str(subnet['AvailableIpAddressCount']) + " available IPs" + " and it should have at least 500")

                notification = "Subnet: *{0}* ".format(checkedSubnet) + subnet['SubnetId'] + " has not enough available IPs" + ", " + "It has " + str(subnet['AvailableIpAddressCount']) + " available IPs" + " and it should have at least 500"

                slack_notification(notification)

              else:
                print("Subnet: " + subnet['SubnetId'] + " has " + str(subnet['AvailableIpAddressCount']) + " available IPs")
                
    except Exception as e:
        print (e)
