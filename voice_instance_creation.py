import boto3

def lambda_handler(event, context):
    ec2 = boto3.resource('ec2', region_name="us-east-1")

    instanceinfo = ec2.create_instances(
        ImageId='ami-9f086de0',
        MinCount=1,
        MaxCount=1,
        KeyName='LambdaEC2',
        SecurityGroupIds=[
            'default'
        ],
        InstanceType='t2.micro'
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
        print(instances.id)
