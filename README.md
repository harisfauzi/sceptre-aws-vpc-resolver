# Overview

The purpose of this resolver is to retrieve VPC ID from the AWS VPC.

## Install

```bash
pip install sceptre-vpc-resolver
```

## Available Resolvers

### aws_vpc

Fetches the VPC ID from a VPC with given tag:Name.

__Note:__ Sceptre must be run with a user or role that has access to the describe VPCs.

Syntax:

```yaml
parameter|sceptre_user_data:
  <name>: !aws_vpc some_vpc_name
```

```yaml
parameter|sceptre_user_data:
  <name>: !aws_vpc
    name: some_vpc_name
    region: us-east-1
    profile: OtherAccount
```

```yaml
parameter|sceptre_user_data:
  <name>: !aws_vpc {"name": "some_vpc_name", "region": "us-east-1", "profile": "OtherAccount"}
```


#### Parameters
* name - VPC tag:Name, mandatory
* region - VPC region, optional, stack region by default
* profile - VPC account profile , optional, stack profile by default

#### Example:

Create a VPC with tag:Name
```bash
aws ec2 create-vpc --cidr-block "10.255.0.0/20" \
--tag-specifications ResourceType=vpc,Tags='[{Key=Name,Value="TestVpc"}]'
```

Retrieve the VPC ID from the same account that the
stack is being deployed to:
```yaml
parameters:
  vpc_id: !aws_vpc TestVpc
```

Retrieve the VPC ID from another AWS account:
```yaml
parameters:
  vpc_id: !aws_vpc
    name: TestVpc
    profile: OtherAccount
```