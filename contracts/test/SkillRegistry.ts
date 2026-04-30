import { expect } from "chai";
import hre from "hardhat";
import { keccak256, toBytes } from "viem";

describe("SkillRegistry", function () {
  async function deployFixture() {
    const [author, otherUser] = await hre.viem.getWalletClients();
    const skillRegistry = await hre.viem.deployContract("SkillRegistry");
    const publicClient = await hre.viem.getPublicClient();
    return { skillRegistry, author, otherUser, publicClient };
  }

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      const { skillRegistry } = await deployFixture();
      expect(skillRegistry.address).to.match(/^0x[a-fA-F0-9]{40}$/);
    });
  });

  describe("registerSkill", function () {
    it("Should register a new skill", async function () {
      const { skillRegistry, author } = await deployFixture();
      const contentHash = keccak256(toBytes("my-first-skill-v1"));
      const ipfsCid = "QmTestCidExample123456789";
      await skillRegistry.write.registerSkill([contentHash, ipfsCid]);
      const skill = await skillRegistry.read.getSkill([contentHash]);
      expect(skill.author.toLowerCase()).to.equal(author.account.address.toLowerCase());
      expect(skill.ipfsCid).to.equal(ipfsCid);
      expect(skill.contentHash).to.equal(contentHash);
    });

    it("Should reject duplicate registration", async function () {
      const { skillRegistry } = await deployFixture();
      const contentHash = keccak256(toBytes("duplicate-skill"));
      const ipfsCid = "QmDuplicateTest";
      await skillRegistry.write.registerSkill([contentHash, ipfsCid]);
      await expect(
        skillRegistry.write.registerSkill([contentHash, ipfsCid])
      ).to.be.rejectedWith("Skill already registered");
    });

    it("Should reject empty IPFS CID", async function () {
      const { skillRegistry } = await deployFixture();
      const contentHash = keccak256(toBytes("no-cid-skill"));
      await expect(
        skillRegistry.write.registerSkill([contentHash, ""])
      ).to.be.rejectedWith("IPFS CID required");
    });

    it("Should reject zero content hash", async function () {
      const { skillRegistry } = await deployFixture();
      const zeroHash = "0x0000000000000000000000000000000000000000000000000000000000000000" as const;
      await expect(
        skillRegistry.write.registerSkill([zeroHash, "QmValidCid"])
      ).to.be.rejectedWith("Invalid content hash");
    });
  });

  describe("getAuthorSkillCount", function () {
    it("Should return zero for new author", async function () {
      const { skillRegistry, otherUser } = await deployFixture();
      const count = await skillRegistry.read.getAuthorSkillCount([otherUser.account.address]);
      expect(count).to.equal(0n);
    });

    it("Should count multiple skills correctly", async function () {
      const { skillRegistry, author } = await deployFixture();
      const hash1 = keccak256(toBytes("skill-one"));
      const hash2 = keccak256(toBytes("skill-two"));
      const hash3 = keccak256(toBytes("skill-three"));
      await skillRegistry.write.registerSkill([hash1, "QmCid1"]);
      await skillRegistry.write.registerSkill([hash2, "QmCid2"]);
      await skillRegistry.write.registerSkill([hash3, "QmCid3"]);
      const count = await skillRegistry.read.getAuthorSkillCount([author.account.address]);
      expect(count).to.equal(3n);
    });
  });
});
