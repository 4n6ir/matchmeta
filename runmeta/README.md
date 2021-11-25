# runmeta

Create blank project for TypeScript development with CDK.

```
$ cdk init app --language typescript
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

 * `npm run build`   compile typescript to js
 * `npm run watch`   watch for changes and compile
 * `npm run test`    perform the jest unit tests
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk synth`       emits the synthesized CloudFormation template

## Setup commands

 * `cd matchmeta/runmeta`
 * `npm install @aws-cdk/aws-ec2`
 * `npm install @aws-cdk/aws-iam`
 * `npm install @aws-cdk/aws-s3`
 * `npm install @aws-cdk/aws-ssm`
 * `npm audit fix`
 * `npm audit fix --force`

## CloudFormation output

 * `cdk synth --no-version-reporting --no-path-metadata --no-asset-metadata > ../template/template.cfn.yaml`