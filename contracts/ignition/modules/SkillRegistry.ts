import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const SkillRegistryModule = buildModule("SkillRegistryModule", (m) => {
  const skillRegistry = m.contract("SkillRegistry");
  return { skillRegistry };
});

export default SkillRegistryModule;
