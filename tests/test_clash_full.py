#!/usr/bin/env python3
"""Regression checks for Clash-Full.ini country-group coverage."""

from pathlib import Path
import re
import unittest

CONFIG = Path(__file__).resolve().parents[1] / "Clash-Full.ini"

CORE_CASES = {
    "香港-自动": ["🇭🇰 香港01", "HK 01", "Hong Kong 01"],
    "台湾-自动": ["🇨🇳 台湾01", "🇹🇼 台灣 01", "Taiwan 01"],
    "日本-自动": ["🇯🇵 日本01", "JP Tokyo", "Japan 01"],
    "新加坡-自动": ["🇸🇬 新加坡01", "SG 01", "Singapore 01"],
    "韩国-自动": ["🇰🇷 韩国01", "KR Seoul", "Korea 01"],
    "美国-自动": ["🇺🇸 美国01", "US Los Angeles", "United States 01"],
}

OTHER_COUNTRIES = [
    "🇩🇪 德国", "🇫🇷 法国", "🇬🇧 英国", "🇮🇳 印度-西部", "🇨🇱 智利",
    "🇧🇷 巴西", "🇪🇸 西班牙", "🇨🇭 瑞士", "🇸🇪 瑞典", "🇲🇽 墨西哥",
    "🇨🇦 加拿大", "🇦🇺 澳大利亚01", "🇦🇪 迪拜", "🇿🇦 南非",
    "🇸🇦 沙特阿拉伯", "🇨🇴 哥伦比亚", "🇮🇱 以色列", "🇻🇳 越南",
    "🇹🇭 泰国", "🇲🇾 马来西亚", "🇷🇺 莫斯科", "🇵🇭 菲律宾",
    "🇳🇬 尼日利亚01", "🇮🇩 印度尼西亚", "🇹🇷 土耳其", "🇬🇷 希腊",
    "🇲🇲 缅甸", "🇵🇰 巴基斯坦", "🇳🇴 挪威", "🇰🇭 柬埔寨",
    "🇪🇬 埃及", "🇮🇶 伊拉克", "🇧🇩 孟加拉", "🇰🇿 哈萨克斯坦",
    "🇦🇷 阿根廷",
    # Future/less-common country names must also have a fallback without edits.
    "🇳🇿 新西兰", "🇵🇹 葡萄牙", "🇫🇮 芬兰", "🇮🇪 爱尔兰",
    "Australia 01", "Russia Moscow 01", "Austria Vienna 01",
    "🇦🇹 奥地利", "🇧🇪 比利时", "🇵🇱 波兰", "🇺🇦 乌克兰",
    "🇷🇴 罗马尼亚", "🇨🇿 捷克", "🇭🇺 匈牙利", "🇩🇰 丹麦",
    "🇮🇸 冰岛", "🇵🇪 秘鲁", "🇺🇾 乌拉圭", "🇵🇦 巴拿马",
    "🇨🇷 哥斯达黎加", "🇶🇦 卡塔尔", "🇰🇼 科威特", "🇯🇴 约旦",
    "🇳🇵 尼泊尔", "🇱🇰 斯里兰卡", "🇲🇳 蒙古", "🇱🇦 老挝",
    "🇧🇳 文莱", "🇫🇯 斐济", "🇰🇪 肯尼亚", "🇲🇦 摩洛哥",
    "🇬🇭 加纳", "🇹🇳 突尼斯", "🇪🇹 埃塞俄比亚",
    "New Zealand 01", "Portugal 01", "United Arab Emirates 01",
]


def load_active_groups():
    groups = {}
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        if not line.startswith("custom_proxy_group="):
            continue
        fields = line.removeprefix("custom_proxy_group=").split("`")
        if len(fields) >= 3:
            groups[fields[0]] = fields[2]
    return groups


class ClashFullCountryCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONFIG.read_text(encoding="utf-8")
        cls.groups = load_active_groups()

    def test_core_country_groups_match_common_names(self):
        for group, names in CORE_CASES.items():
            self.assertIn(group, self.groups)
            pattern = re.compile(self.groups[group], re.IGNORECASE)
            for name in names:
                with self.subTest(group=group, name=name):
                    self.assertRegex(name, pattern)

    def test_other_group_is_future_proof_for_every_non_core_country(self):
        pattern = re.compile(self.groups["其他-自动"], re.IGNORECASE)
        for name in OTHER_COUNTRIES:
            with self.subTest(name=name):
                self.assertRegex(name, pattern)

    def test_other_group_excludes_core_countries(self):
        pattern = re.compile(self.groups["其他-自动"], re.IGNORECASE)
        for names in CORE_CASES.values():
            for name in names:
                with self.subTest(name=name):
                    self.assertNotRegex(name, pattern)

    def test_all_referenced_proxy_groups_exist(self):
        defined = set(self.groups) | {"DIRECT", "REJECT"}
        for line in self.text.splitlines():
            if not line.startswith("custom_proxy_group="):
                continue
            group_name = line.split("`", 1)[0].split("=", 1)[1]
            for reference in re.findall(r"\[\]([^`]+)", line):
                with self.subTest(group=group_name, reference=reference):
                    self.assertIn(reference, defined)

    def test_rule_urls_do_not_contain_nested_http(self):
        self.assertNotIn("gh-proxy.com/http://", self.text)

    def test_openai_domains_have_inline_rules_before_remote_providers(self):
        """Critical AI routing must survive a failed remote rule-provider download."""
        lines = self.text.splitlines()
        required = {
            "ruleset=✨ AI1,[]DOMAIN-SUFFIX,openai.com",
            "ruleset=✨ AI1,[]DOMAIN-SUFFIX,chatgpt.com",
            "ruleset=✨ AI1,[]DOMAIN-SUFFIX,oaistatic.com",
            "ruleset=✨ AI1,[]DOMAIN-SUFFIX,oaiusercontent.com",
        }
        positions = {line: lines.index(line) for line in required if line in lines}
        self.assertEqual(set(positions), required)
        remote_ai = next(i for i, line in enumerate(lines) if line.startswith("ruleset=✨ AI1,http"))
        self.assertTrue(all(position < remote_ai for position in positions.values()))

    def test_required_generator_flags_are_enabled(self):
        self.assertIn("enable_rule_generator=true", self.text)
        self.assertIn("overwrite_original_rules=true", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
