import asyncio
from typing import Optional

import discord
from loguru import logger

import del_spam.config as config
from del_spam.filter import FilterEngine


class MessageDeleter:
    def __init__(self, filter_engine: FilterEngine):
        self.filter_engine = filter_engine
        self.dry_run = config.DRY_RUN
        self.max_deletions = config.MAX_DELETIONS_PER_RUN
        self.batch_size = config.BATCH_SIZE
        self.api_call_interval = config.API_CALL_INTERVAL

    async def delete_by_rule(
        self, bot: discord.Client, rule_name: str, guild: Optional[discord.Guild] = None
    ) -> int:
        logger.info(f"Starting deletion for rule: {rule_name}")
        logger.info(f"Dry run: {self.dry_run}")

        if rule_name not in self.filter_engine.filters:
            logger.error(f"Rule not found: {rule_name}")
            return 0

        deleted_count = 0

        guilds_to_process = []
        if guild is not None:
            guilds_to_process = [guild]
        else:
            guilds_to_process = bot.guilds

        if not guilds_to_process:
            logger.error("No guilds accessible")
            return 0

        logger.info(f"Processing {len(guilds_to_process)} guild(s)")

        for target_guild in guilds_to_process:
            if deleted_count >= self.max_deletions:
                logger.info(f"Reached maximum deletions limit ({self.max_deletions})")
                break

            logger.info(
                f"Processing guild: {target_guild.name} (ID: {target_guild.id})"
            )

            for channel in target_guild.text_channels:
                if deleted_count >= self.max_deletions:
                    logger.info(
                        f"Reached maximum deletions limit ({self.max_deletions})"
                    )
                    break

                try:
                    async for message in channel.history(limit=None):
                        if deleted_count >= self.max_deletions:
                            break

                        if self.filter_engine.matches_rule(rule_name, message):
                            deleted_count += 1

                            if self.dry_run:
                                logger.info(
                                    f"[DRY RUN] Would delete message {message.id} "
                                    f"from {message.author} in #{channel.name}: "
                                    f"{message.content[:50]}"
                                )
                            else:
                                try:
                                    await message.delete()
                                    logger.info(
                                        f"Deleted message {message.id} from {message.author} "
                                        f"in #{channel.name}: {message.content[:50]}"
                                    )
                                except discord.NotFound:
                                    logger.warning(f"Message {message.id} not found")
                                except discord.Forbidden:
                                    logger.error(
                                        f"Permission denied to delete {message.id}"
                                    )
                                except Exception as e:
                                    logger.error(
                                        f"Failed to delete message {message.id}: {e}"
                                    )

                            await asyncio.sleep(self.api_call_interval)

                except discord.Forbidden:
                    logger.warning(
                        f"Permission denied for channel: {channel.name} in {target_guild.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing channel {channel.name} in {target_guild.name}: {e}"
                    )

            logger.info(f"Completed processing guild: {target_guild.name}")

        logger.info(f"Deletion completed. Total: {deleted_count} messages")
        return deleted_count

    async def delete_by_rules(
        self,
        bot: discord.Client,
        rule_names: list[str],
        guild: Optional[discord.Guild] = None,
    ) -> int:
        total_deleted = 0
        for rule_name in rule_names:
            deleted = await self.delete_by_rule(bot, rule_name, guild)
            total_deleted += deleted
        return total_deleted
