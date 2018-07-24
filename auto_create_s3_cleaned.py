import boto3
import json, re, sys

def createUser (client, name):
    response = client.create_user(
        Path = '/',
        UserName = name
    )
    return response
#End createUser
def addUserToGroup(client, group, user):
    response = client.add_user_to_group(
        GroupName=group,
        UserName=user
    )
    return response
#End addUserToGroup
def generateKeys(client, name):
    response = client.create_access_key(
        UserName = name
    )
    return response
#End generateKeys
def createGroup (client, name):
    response = client.create_group(
        Path = '/',
        GroupName = name
    )
    return response
#End createGroup
def attachGroupPolicy(client, name, arn):
    response = client.attach_group_policy(
        GroupName = name,
        PolicyArn = arn
    )
    return response
#End attachGroupPolicy
def createPolicy (client, name, policy, desc):
    response = client.create_policy(
        PolicyName = name,
        Path = '/',
        PolicyDocument = policy,
        Description = desc,
    )
    return response
#End createPolicy
def createBucket (client, name, policy, location = ''):
    bucket = ''
    if (location == ''):
        bucket = client.create_bucket(
            Bucket=name,
            ACL='log-delivery-write'
        )
    else:
        bucket == client.create_bucket(
            Bucket=name,
            ACL='log-delivery-write',
            CreateBucketConfiguration = {
                'LocationConstraint': location
            },
        )
    return bucket

#End createBucket
def enableBucketLogging (client, name, policy):
    response = client.put_bucket_logging(
        Bucket = name,
        BucketLoggingStatus = policy,
    )
    return response
#End enableBucketLogging
def createFile(user, items = []):
    filename = user + ".csv"
    f = open(filename, 'w')
    f.write("User name,Access key ID,Secret access key\n")
    f.write(user + ",")
    for i in items:
        f.write(i + ",")
    f.write("\n")
    f.close()
    return 0
#End createFile
def removeDateErrors(mydict):
    for i in mydict:
        if (type(mydict[i]) is dict):
            for k in mydict[i]:
                if (k == 'CreateDate' or k == 'UpdateDate'):
                    mydict[i][k] = ''
        elif(type(mydict[i]) is tuple):
            for k in mydict[i]:
                for j in mydict[i][k]:
                    if (j == 'CreateDate' or j == 'UpdateDate'):
                        mydict[i][k][j] = ''
    return mydict
#End removeDateErrors


#############################################################################
#Edit the stuff in here, but like carefully##################################
#############################################################################
#All you gots to do is edit the uesrname, preferably with first initial + last name

#print ("arguments: ", sys.argv[1])
if (len(sys.argv) < 2):
    print ("Usage: " + sys.argv[0] + " bucket.name\n")
    sys.exit()
    
user = sys.argv[1]#edit me

#ignore the if
if (user == ''):
    print("User was not set.")
    sys.exit()

iam_user_name = "QA_Media_Server_" + user
iam_group_name = "TW_QA_Group_" + user
iam_policy_name = "<REDACTED>_QA_Media_Server_Policy_" + user
iam_policy_desc = "Attached storage for Functional QA Testing Group - Requested by " + user
iam_policy_arn = ""#should be empty string

s3_bucket_name = "media-tw-" + user
s3_bucket_region = "us-west-1"
s3_bucket_log_prefix = 'logs/' + user

s3_bucket_logging_policy_json = {
    'LoggingEnabled': {
        'TargetBucket': s3_bucket_name,
        'TargetPrefix': s3_bucket_log_prefix
    }
}

iam_policy_json = """{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": "s3:*","Resource": "arn:aws:s3:::%s*"}]}""" % (s3_bucket_name)

print ("Username: " + iam_user_name + "\n")
print ("Group Name: " + iam_group_name + "\n")
print ("Policy Name: " + iam_policy_name + "\n")
print ("Policy Desc: " + iam_policy_desc + "\n")
print ("Bucket Name: " + s3_bucket_name + "\n")
print ("Bucket Region: " + s3_bucket_region + "\n")
print ("Log Prefix: " + s3_bucket_log_prefix + "\n")
print ("\n")
check = input("Does this information look correct (y/N): ")
if (check == 'y' or check == 'Y' or check == 'yes'):
    print ("Doing it boss!\n")
else:
    sys.exit()


iam_client = boto3.client('iam',
        aws_access_key_id='',#account
        aws_secret_access_key='',#secret key for that account, shhhhhhhhhhh
    )
s3_client = boto3.client( 's3',
        aws_access_key_id='',#account
        aws_secret_access_key='',#secret key for that account, shhhhhhhhhhh
        
    )
#############################################################################
#Your eyes are straying, look back up########################################
#############################################################################

#create bucket
response = createBucket(s3_client, s3_bucket_name, s3_bucket_logging_policy_json, s3_bucket_region)

#Enable logging on bucket
response = enableBucketLogging(s3_client, s3_bucket_name, s3_bucket_logging_policy_json)

#Create Policy and retrieve policy arn from response
policyInfo = createPolicy (iam_client, iam_policy_name, iam_policy_json, iam_policy_desc)
iam_policy_arn = policyInfo['Policy']['Arn']

#createGroup
response = createGroup(iam_client, iam_group_name)

#Attach group policy
response = attachGroupPolicy(iam_client, iam_group_name, iam_policy_arn)

#Create User
response = createUser(iam_client, iam_user_name)
#print ("create User: ", json.dumps(removeDateErrors(response), sort_keys=True,indent=4, separators=(',', ': ')))

#Add user to group
response = addUserToGroup(iam_client, iam_group_name, iam_user_name)
#print ("Add User to group: ", json.dumps(removeDateErrors(response), sort_keys=True,indent=4, separators=(',', ': ')))

#create access keys
response = generateKeys(iam_client, iam_user_name)
iam_access_key = response['AccessKey']['AccessKeyId']
iam_secret_access_key = response['AccessKey']['SecretAccessKey']

#write keys to file
status = createFile(s3_bucket_name, [iam_access_key, iam_secret_access_key])

print ("Access key: " + iam_access_key)
print ("Secret Access key: " + iam_secret_access_key)
print ("Bucket Name: " + s3_bucket_name)
