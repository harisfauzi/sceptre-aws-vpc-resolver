# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock, patch, sentinel

from botocore.exceptions import ClientError

from sceptre.connection_manager import ConnectionManager
from sceptre.stack import Stack

from resolver.aws_vpc import AwsVpc, AwsVpcBase
from resolver.aws_vpc_exceptions import VPCNotFoundError


region = 'us-east-1'


class TestVpcResolver(object):
    def test_resolve_str_arg_no_param_name(self):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_vpc_resolver = AwsVpc(
            None, stack
        )
        with pytest.raises(ValueError):
            stack_vpc_resolver.resolve()

    def test_resolve_obj_arg_no_param_name(self):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_vpc_resolver = AwsVpc(
            {}, stack
        )
        with pytest.raises(ValueError):
            stack_vpc_resolver.resolve()

    @patch(
        "resolver.aws_vpc.AwsVpc._get_vpc_id"
    )
    def test_resolve_str_arg(self, mock_get_vpc_id):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.region = region
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_vpc_resolver = AwsVpc(
            "TestVPC", stack
        )
        mock_get_vpc_id.return_value = "vpc-01234567890123456"
        stack_vpc_resolver.resolve()
        mock_get_vpc_id.assert_called_once_with(
            "TestVPC", region, "test_profile"
        )

    @patch(
        "resolver.aws_vpc.AwsVpc._get_vpc_id"
    )
    def test_resolve_obj_arg_no_profile(self, mock_get_vpc_id):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.region = region
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_vpc_resolver = AwsVpc(
            {"name": "TestVPC"}, stack
        )
        mock_get_vpc_id.return_value = "vpc-01234567890123456"
        stack_vpc_resolver.resolve()
        mock_get_vpc_id.assert_called_once_with(
            "TestVPC", region, "test_profile"
        )

    @patch(
        "resolver.aws_vpc.AwsVpc._get_vpc_id"
    )
    def test_resolve_obj_arg_profile_override(self, mock_get_vpc_id):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.region = region
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_vpc_resolver = AwsVpc(
            {"name": "TestVPC", "profile": "new_profile"}, stack
        )
        mock_get_vpc_id.return_value = "vpc-01234567890123456"
        stack_vpc_resolver.resolve()
        mock_get_vpc_id.assert_called_once_with(
            "TestVPC", region, "new_profile"
        )

    @patch(
        "resolver.aws_vpc.AwsVpc._get_vpc_id"
    )
    def test_resolve_obj_arg_region_override(self, mock_get_vpc_id):
        stack = MagicMock(spec=Stack)
        stack.profile = "test_profile"
        stack.region = region
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)

        custom_region = 'ap-southeast-1'
        assert custom_region != region

        stack_vpc_resolver = AwsVpc(
            {
                "name": "TestVPC",
                "region": custom_region,
                "profile": "new_profile"
            },
            stack
        )
        mock_get_vpc_id.return_value = "vpc-01234567890123456"
        stack_vpc_resolver.resolve()
        mock_get_vpc_id.assert_called_once_with(
            "TestVPC", custom_region, "new_profile"
        )


class MockAwsVpcBase(AwsVpcBase):
    """
    MockBaseResolver inherits from the abstract base class
    AwsVpcBase, and implements the abstract methods. It is used
    to allow testing on AwsVpcBase, which is not otherwise
    instantiable.
    """

    def __init__(self, *args, **kwargs):
        super(MockAwsVpcBase, self).__init__(*args, **kwargs)

    def resolve(self):
        pass


class TestAwsVpcBase(object):

    def setup_method(self, test_method):
        self.stack = MagicMock(spec=Stack)
        self.stack.name = "test_name"
        self.stack._connection_manager = MagicMock(
            spec=ConnectionManager
        )
        self.base_vpc = MockAwsVpcBase(
            None, self.stack
        )

    @patch(
        "resolver.aws_vpc.AwsVpcBase._request_vpc"
    )
    def test_get_vpc_id_with_valid_key(self, mock_request_vpc):
        mock_request_vpc.return_value = {
            "Vpcs": [
                {
                    "CidrBlock": "10.255.0.0/20",
                    "DhcpOptionsId": "dopt-01234567",
                    "State": "available",
                    "VpcId": "vpc-01234567890123456",
                    "OwnerId": "111111111111",
                    "InstanceTenancy": "default",
                    "CidrBlockAssociationSet": [
                        {
                            "AssociationId": "vpc-cidr-assoc-01234567890123456",
                            "CidrBlock": "10.255.0.0/20",
                            "CidrBlockState": {
                                "State": "associated"
                            }
                        }
                    ],
                    "IsDefault": False,
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "TestVPC"
                        }
                    ]
                }
            ]
        }
        response = self.base_vpc._get_vpc_id("TestVPC", region)
        assert response == "vpc-01234567890123456"

    @patch(
        "resolver.aws_vpc.AwsVpcBase._request_vpc"
    )
    def test_get_vpc_id_with_invalid_response(self, mock_request_vpc):
        mock_request_vpc.return_value = {
            "Vpcs": [
                {
                    "CidrBlock": "10.255.0.0/20",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "TestVPC"
                        }
                    ]
                }
            ]
        }

        with pytest.raises(KeyError):
            self.base_vpc._get_vpc_id(None, region)

    def test_request_vpc_with_unkown_boto_error(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "500",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )

        with pytest.raises(ClientError):
            self.base_vpc._request_vpc(None, region)

    def test_request_vpc_with_vpc_not_found(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "VpcNotFound",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )

        with pytest.raises(VPCNotFoundError):
            self.base_vpc._request_vpc(None, region)