// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title SkillRegistry
 * @notice On-chain registry for Hermes Agent skills.
 *         Stores who registered which skill and when, with IPFS pointer.
 */
contract SkillRegistry {
    
    // Bir skill'in tüm bilgileri
    struct Skill {
        address author;       // Yazarın wallet adresi
        bytes32 contentHash;  // Skill içeriğinin hash'i (kimliği)
        string ipfsCid;       // IPFS'teki konumu
        uint256 registeredAt; // Kayıt zamanı (block timestamp)
    }
    
    // Hash'ten skill'e mapping (anahtar = contentHash)
    mapping(bytes32 => Skill) public skills;
    
    // Yazardan skill listesine mapping
    mapping(address => bytes32[]) public skillsByAuthor;
    
    // Yeni skill kaydedildiğinde tetiklenen olay
    event SkillRegistered(
        bytes32 indexed contentHash,
        address indexed author,
        string ipfsCid,
        uint256 registeredAt
    );
    
    /**
     * @notice Yeni bir skill'i kayıt et
     * @param contentHash Skill içeriğinin keccak256 hash'i
     * @param ipfsCid Skill'in IPFS adresi
     */
    function registerSkill(bytes32 contentHash, string calldata ipfsCid) external {
        // Bu hash daha önce kayıtlı mı?
        require(skills[contentHash].author == address(0), "Skill already registered");
        require(contentHash != bytes32(0), "Invalid content hash");
        require(bytes(ipfsCid).length > 0, "IPFS CID required");
        
        // Skill'i kaydet
        skills[contentHash] = Skill({
            author: msg.sender,
            contentHash: contentHash,
            ipfsCid: ipfsCid,
            registeredAt: block.timestamp
        });
        
        // Yazarın listesine ekle
        skillsByAuthor[msg.sender].push(contentHash);
        
        // Olayı duyur
        emit SkillRegistered(contentHash, msg.sender, ipfsCid, block.timestamp);
    }
    
    /**
     * @notice Bir hash'in skill bilgilerini getir
     */
    function getSkill(bytes32 contentHash) external view returns (Skill memory) {
        return skills[contentHash];
    }
    
    /**
     * @notice Bir yazarın kaç skill'i var?
     */
    function getAuthorSkillCount(address author) external view returns (uint256) {
        return skillsByAuthor[author].length;
    }
}
