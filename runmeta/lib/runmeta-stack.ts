import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export class RunmetaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'TemporaryVPC', {
      ipAddresses: ec2.IpAddresses.cidr('192.168.42.0/24'),
      maxAzs: 1,
      natGateways: 0,
      enableDnsHostnames: true,
      enableDnsSupport: true,
      subnetConfiguration: [
        {
          subnetType: ec2.SubnetType.PUBLIC,
          name: 'Public',
          cidrMask: 24,
        }
      ],
    });

    const linux = ec2.MachineImage.fromSsmParameter('/matchmeta/ssm/ami');

    const ec2type = ssm.StringParameter.fromStringParameterAttributes(this, 'ec2type', {
      parameterName: '/matchmeta/ssm/ec2type'
    }).stringValue;

    const archtype = ssm.StringParameter.fromStringParameterAttributes(this, 'archtype', {
      parameterName: '/matchmeta/ssm/arch'
    }).stringValue;

    const dwarf = ssm.StringParameter.fromStringParameterAttributes(this, 'dwarf', {
      parameterName: '/matchmeta/bucket/dwarf'
    }).stringValue;
    
    const raw = ssm.StringParameter.fromStringParameterAttributes(this, 'raw', {
      parameterName: '/matchmeta/bucket/raw'
    }).stringValue;

    const role = new iam.Role(this, 'TemporaryRole', {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
    });

    role.addToPolicy(new iam.PolicyStatement({
      resources: ['*'],
      actions: [
        's3:ListBucket',
        's3:GetBucketAcl',
        's3:GetObject',
        's3:PutObject'
      ],
    }));

    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName(
        'AmazonSSMManagedInstanceCore'
      )
    );

    const multipartUserData = new ec2.MultipartUserData();
    const commandsUserData = ec2.UserData.forLinux();
    multipartUserData.addUserDataPart(commandsUserData, ec2.MultipartBody.SHELL_SCRIPT, true);

    commandsUserData.addCommands('yum install file-devel python3-pip unzip wget -y');
    commandsUserData.addCommands('wget https://awscli.amazonaws.com/awscli-exe-linux-'+archtype+'.zip -P /tmp/');
    commandsUserData.addCommands('unzip /tmp/awscli-exe-linux-'+archtype+'.zip -d /tmp');
    commandsUserData.addCommands('./tmp/aws/install');
    commandsUserData.addCommands('aws s3 cp /boot/System* s3://'+dwarf);
    commandsUserData.addCommands('pip3 install getmeta');
    commandsUserData.addCommands('cd /tmp && getmeta');
    commandsUserData.addCommands('aws s3 cp /tmp/ip-* s3://'+raw);

    const instance = new ec2.Instance(this, 'TemporaryEC2', {
      instanceType: new ec2.InstanceType(ec2type),
      machineImage: linux,
      vpc: vpc,
      role: role,
      requireImdsv2: true,
      userData: multipartUserData,
    });

  }
}
