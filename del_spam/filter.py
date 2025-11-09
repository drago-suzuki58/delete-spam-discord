import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import discord
from loguru import logger


class FilterType(Enum):
    GUILD = "guild"
    CHANNEL = "channel"
    USER = "user"
    ROLE = "role"
    MESSAGE_ID = "message_id"
    TIMESTAMP = "timestamp"
    CONTENT = "content"
    GROUP = "group"


class Operator(Enum):
    IN = "IN"
    NOT_IN = "NOT_IN"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    BETWEEN = "BETWEEN"
    AFTER = "AFTER"
    BEFORE = "BEFORE"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    REGEX = "REGEX"
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"


def parse_timestamp(timestamp_str: str) -> datetime:
    timestamp_str = timestamp_str.rstrip("Z")
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        logger.error(f"Invalid timestamp format: {timestamp_str}")
        raise


def normalize_value(value: Any) -> int | str:
    if isinstance(value, (int, str)):
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value
    return value


@dataclass
class Filter:
    type: FilterType
    operator: Operator
    values: Any = None
    start: str | None = None
    end: str | None = None

    def matches(
        self, message: discord.Message, member: discord.Member | None = None
    ) -> bool:
        try:
            if self.type == FilterType.GUILD:
                return self._match_guild(message)
            elif self.type == FilterType.CHANNEL:
                return self._match_channel(message)
            elif self.type == FilterType.USER:
                return self._match_user(message)
            elif self.type == FilterType.ROLE:
                return self._match_role(message, member)
            elif self.type == FilterType.MESSAGE_ID:
                return self._match_message_id(message)
            elif self.type == FilterType.TIMESTAMP:
                return self._match_timestamp(message)
            elif self.type == FilterType.CONTENT:
                return self._match_content(message)
            else:
                logger.warning(f"Unknown filter type: {self.type}")
                return False
        except Exception as e:
            logger.error(f"Error in filter matching: {e}")
            return False

    def _match_guild(self, message: discord.Message) -> bool:
        if message.guild is None:
            return False

        guild_id = message.guild.id
        values = self._normalize_values(self.values)

        if self.operator == Operator.IN:
            return guild_id in values
        elif self.operator == Operator.NOT_IN:
            return guild_id not in values
        elif self.operator == Operator.EQUALS:
            return guild_id == values[0] if values else False
        elif self.operator == Operator.NOT_EQUALS:
            return guild_id != values[0] if values else False
        return False

    def _match_channel(self, message: discord.Message) -> bool:
        channel_id = message.channel.id
        values = self._normalize_values(self.values)

        if self.operator == Operator.IN:
            return channel_id in values
        elif self.operator == Operator.NOT_IN:
            return channel_id not in values
        elif self.operator == Operator.EQUALS:
            return channel_id == values[0] if values else False
        elif self.operator == Operator.NOT_EQUALS:
            return channel_id != values[0] if values else False
        return False

    def _match_user(self, message: discord.Message) -> bool:
        user_id = message.author.id
        values = self._normalize_values(self.values)

        if self.operator == Operator.IN:
            return user_id in values
        elif self.operator == Operator.NOT_IN:
            return user_id not in values
        elif self.operator == Operator.EQUALS:
            return user_id == values[0] if values else False
        elif self.operator == Operator.NOT_EQUALS:
            return user_id != values[0] if values else False
        return False

    def _match_role(
        self, message: discord.Message, member: discord.Member | None
    ) -> bool:
        if member is None and isinstance(message.author, discord.Member):
            member = message.author

        if member is None:
            return False

        role_ids = [role.id for role in member.roles]
        values = self._normalize_values(self.values)

        if self.operator == Operator.IN:
            return any(role_id in values for role_id in role_ids)
        elif self.operator == Operator.NOT_IN:
            return not any(role_id in values for role_id in role_ids)
        elif self.operator == Operator.EQUALS:
            return values[0] in role_ids if values else False
        elif self.operator == Operator.NOT_EQUALS:
            return values[0] not in role_ids if values else False
        return False

    def _match_message_id(self, message: discord.Message) -> bool:
        message_id = message.id
        values = self._normalize_values(self.values)

        if self.operator == Operator.IN:
            return message_id in values
        elif self.operator == Operator.NOT_IN:
            return message_id not in values
        elif self.operator == Operator.EQUALS:
            return message_id == values[0] if values else False
        elif self.operator == Operator.NOT_EQUALS:
            return message_id != values[0] if values else False
        return False

    def _match_timestamp(self, message: discord.Message) -> bool:
        msg_timestamp = message.created_at.replace(tzinfo=None)

        if self.operator == Operator.BETWEEN:
            if not self.start or not self.end:
                return False
            start = parse_timestamp(self.start)
            end = parse_timestamp(self.end)
            return start <= msg_timestamp <= end

        elif self.operator == Operator.AFTER:
            if not self.start:
                return False
            start = parse_timestamp(self.start)
            return msg_timestamp >= start

        elif self.operator == Operator.BEFORE:
            if not self.end:
                return False
            end = parse_timestamp(self.end)
            return msg_timestamp <= end

        return False

    def _match_content(self, message: discord.Message) -> bool:
        content = message.content.lower()
        values = self.values if isinstance(self.values, list) else [self.values]

        if self.operator == Operator.CONTAINS:
            return any(str(v).lower() in content for v in values)
        elif self.operator == Operator.NOT_CONTAINS:
            return not any(str(v).lower() in content for v in values)
        elif self.operator == Operator.STARTS_WITH:
            return any(content.startswith(str(v).lower()) for v in values)
        elif self.operator == Operator.ENDS_WITH:
            return any(content.endswith(str(v).lower()) for v in values)
        elif self.operator == Operator.REGEX:
            try:
                return any(re.search(str(v), content) for v in values)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return False
        return False

    def _normalize_values(self, values: Any) -> list:
        if values is None:
            return []
        if isinstance(values, list):
            return [normalize_value(v) for v in values]
        return [normalize_value(values)]


class FilterGroup:
    def __init__(self, operator: str, filters: List[Any]):
        self.operator = operator  # "AND" or "OR"
        self.filters = filters

    def matches(
        self, message: discord.Message, member: discord.Member | None = None
    ) -> bool:
        if self.operator == "AND":
            return all(f.matches(message, member) for f in self.filters)
        elif self.operator == "OR":
            return any(f.matches(message, member) for f in self.filters)
        return False


class FilterEngine:
    def __init__(self):
        self.filters: Dict[str, FilterGroup] = {}

    def load_rule(self, rule_name: str, rule_config: Dict):
        if not rule_config.get("enabled", False):
            logger.info(f"Skipping disabled rule: {rule_name}")
            return

        conditions = rule_config.get("conditions", {})
        operator = conditions.get("operator", "AND")
        filters = self._build_filters(conditions.get("filters", []))
        self.filters[rule_name] = FilterGroup(operator, filters)
        logger.info(f"Loaded rule: {rule_name}")

    def _build_filters(self, filter_list: List[Dict]) -> List[Any]:
        result = []
        for filter_def in filter_list:
            try:
                if filter_def.get("type") == "group":
                    nested_filters = self._build_filters(
                        filter_def.get("conditions", [])
                    )
                    result.append(
                        FilterGroup(filter_def.get("operator", "AND"), nested_filters)
                    )
                else:
                    filter_type = filter_def.get("type", "").lower()
                    operator_str = filter_def.get("operator", "").upper()

                    try:
                        filter_type_enum = FilterType[filter_type.upper()]
                    except KeyError:
                        logger.error(f"Unknown filter type: {filter_type}")
                        continue

                    try:
                        operator_enum = Operator[operator_str]
                    except KeyError:
                        logger.error(f"Unknown operator: {operator_str}")
                        continue

                    result.append(
                        Filter(
                            type=filter_type_enum,
                            operator=operator_enum,
                            values=filter_def.get("values"),
                            start=filter_def.get("start"),
                            end=filter_def.get("end"),
                        )
                    )
            except Exception as e:
                logger.error(f"Error building filter: {e}")
                continue

        return result

    def matches_rule(
        self,
        rule_name: str,
        message: discord.Message,
        member: discord.Member | None = None,
    ) -> bool:
        if rule_name not in self.filters:
            return False
        return self.filters[rule_name].matches(message, member)

    def get_matching_rules(
        self,
        message: discord.Message,
        member: discord.Member | None = None,
    ) -> List[str]:
        return [
            rule_name
            for rule_name in self.filters
            if self.matches_rule(rule_name, message, member)
        ]

    def load_all_rules(self, rules: Dict[str, Dict]) -> None:
        for rule_name, rule_config in rules.items():
            self.load_rule(rule_name, rule_config)
        logger.info(f"Loaded {len(self.filters)} rules")
