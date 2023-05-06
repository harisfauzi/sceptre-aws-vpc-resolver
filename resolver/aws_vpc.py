# -*- coding: utf-8 -*-

import abc
import six
import logging

from botocore.exceptions import ClientError
from sceptre.resolvers import Resolver
from resolver.aws_vpc_exceptions import VPCNotFoundError

TEMPLATE_EXTENSION = ".yaml"


@six.add_metaclass(abc.ABCMeta)
class AwsVpcBase(Resolver):
    """
    A abstract base class which provides methods for getting VPC ID.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(AwsVpcBase, self).__init__(*args, **kwargs)

    def _get_vpc_id(self, param, region, profile=None):
        """
        Attempts to get the VPC ID with tag:Name by ``param``
        :param param: The tag:Name of the VPC in which to return.
        :type param: str
        :returns: VPC ID.
        :rtype: str
        :raises: KeyError
        """
        response = self._request_vpc(param, region, profile)

        try:
            self.logger.debug("Got response: {0}".format(response))
            return response['Vpcs'][0]['VpcId']
        except KeyError:
            self.logger.error("%s - Invalid response looking for: %s",
                              self.stack.name, param)
            raise

    def _request_vpc(self, param, region, profile=None):
        """
        Communicates with AWS EC2 to fetch VPC Information.
        :returns: The JSON block of the VPC info
        :rtype: dict
        :raises: resolver.exceptions.VPCNotFoundError
        """
        connection_manager = self.stack.connection_manager

        try:
            self.logger.debug("Calling ec2.describe_vpcs")
            response = connection_manager.call(
                service="ec2",
                command="describe_vpcs",
                kwargs={"Filters": [
                        {
                            "Name": "tag:Name",
                            "Values": [param]
                        }
                    ]
                },
                region=region,
                profile=profile
            )
            self.logger.debug("Finished calling ec2.describe_vpcs")
        except ClientError as e:
            if "VpcNotFound" in e.response["Error"]["Code"]:
                self.logger.error("%s - VpcNotFound: %s",
                                  self.stack.name, param)
                raise VPCNotFoundError(e.response["Error"]["Message"])
            else:
                raise e
        except Exception as err:
            print(f"Unexpected {err}, {type(err)}")
            raise
            
        else:
            return response


class AwsVpc(AwsVpcBase):
    """
    Resolver for retrieving the value of VPC ID.
    :param argument: The VPC tag:Name to get.
    :type argument: str
    """

    def __init__(self, *args, **kwargs):
        super(AwsVpc, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves the value of VPC info
        :returns: The decoded value of the VPC info
        :rtype: str
        """
        args = self.argument
        if not args:
            raise ValueError("Missing argument")

        vpc_id = None
        self.logger.debug(
            "Resolving VPC with argument: {0}".format(args)
        )
        name = self.argument
        region = self.stack.region
        profile = self.stack.profile
        if isinstance(args, dict):
            if 'name' in args:
                name = args['name']
            else:
                raise ValueError("Missing VPC tag:Name")

            profile = args.get('profile', profile)
            region = args.get('region', region)

        self.logger.debug("Resolving VPC with name: {0}".format(name))
        vpc_id = self._get_vpc_id(name, region, profile)
        return vpc_id