// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title LandRegistry
 * @notice On-chain land and property records for demo / academic use (Ganache).
 */
contract LandRegistry {

    struct Property {
        uint256 id;
        string propertyNumber;
        string surveyNumber;
        string ownerName;
        string location;
        uint256 area;
        string propertyType;
        address ownerWallet;
        bytes32 documentHash;
    }

    uint256 public propertyCount;

    mapping(uint256 => Property) public properties;

    event PropertyRegistered(
        uint256 indexed propertyId,
        string propertyNumber,
        string surveyNumber,
        string ownerName,
        address indexed ownerWallet
    );

    event OwnershipTransferred(
        uint256 indexed propertyId,
        address indexed oldOwner,
        address indexed newOwner,
        string newOwnerName
    );

    function registerProperty(
        string memory _propertyNumber,
        string memory _surveyNumber,
        string memory _ownerName,
        string memory _location,
        uint256 _area,
        string memory _propertyType,
        bytes32 _documentHash
    ) public {
        require(bytes(_propertyNumber).length > 0, "Property number required");
        require(bytes(_surveyNumber).length > 0, "Survey number required");
        require(bytes(_ownerName).length > 0, "Owner name required");
        require(_area > 0, "Area must be positive");

        propertyCount++;

        properties[propertyCount] = Property(
            propertyCount,
            _propertyNumber,
            _surveyNumber,
            _ownerName,
            _location,
            _area,
            _propertyType,
            msg.sender,
            _documentHash
        );

        emit PropertyRegistered(
            propertyCount,
            _propertyNumber,
            _surveyNumber,
            _ownerName,
            msg.sender
        );
    }

    function getProperty(uint256 _propertyId)
        public
        view
        returns (
            uint256 id,
            string memory propertyNumber,
            string memory surveyNumber,
            string memory ownerName,
            string memory location,
            uint256 area,
            string memory propertyType,
            address ownerWallet,
            bytes32 documentHash
        )
    {
        require(_propertyId > 0 && _propertyId <= propertyCount, "Invalid property ID");
        Property memory property = properties[_propertyId];
        return (
            property.id,
            property.propertyNumber,
            property.surveyNumber,
            property.ownerName,
            property.location,
            property.area,
            property.propertyType,
            property.ownerWallet,
            property.documentHash
        );
    }

    function transferOwnership(
        uint256 _propertyId,
        address _newOwner,
        string memory _newOwnerName
    ) public {
        require(
            _propertyId > 0 && _propertyId <= propertyCount,
            "Invalid property ID"
        );
        require(
            properties[_propertyId].ownerWallet == msg.sender,
            "Not the property owner"
        );
        require(_newOwner != address(0), "Invalid owner address");
        require(bytes(_newOwnerName).length > 0, "New owner name required");

        address oldOwner = properties[_propertyId].ownerWallet;

        properties[_propertyId].ownerWallet = _newOwner;
        properties[_propertyId].ownerName = _newOwnerName;

        emit OwnershipTransferred(
            _propertyId,
            oldOwner,
            _newOwner,
            _newOwnerName
        );
    }

    function propertyExists(uint256 _propertyId) public view returns (bool) {
        return _propertyId > 0 && _propertyId <= propertyCount;
    }
}
