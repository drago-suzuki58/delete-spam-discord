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
        self.batch_size = config.BULK_DELETE_MAX
        self.api_call_interval = config.API_CALL_INTERVAL

    async def _bulk_delete_messages(
        self, channel: discord.TextChannel, message_ids: list[int]
    ) -> int:
        if not message_ids:
            return 0

        try:
            await channel.delete_messages(
                [discord.Object(msg_id) for msg_id in message_ids]
            )
            logger.info(
                f"Bulk deleted {len(message_ids)} messages from #{channel.name}"
            )
            return len(message_ids)
        except discord.NotFound:
            logger.warning("Some messages in batch not found")
            return len(message_ids)
        except discord.Forbidden:
            logger.error(f"Permission denied to bulk delete in #{channel.name}")
            return 0
        except Exception as e:
            logger.error(f"Failed to bulk delete messages in #{channel.name}: {e}")
            return 0

    async def delete_by_rule(
        self, bot: discord.Client, rule_name: str, guild: Optional[discord.Guild] = None
    ) -> int:
        logger.info(f"Starting deletion for rule: {rule_name}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Using bulk delete API (batch size: {self.batch_size})")

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
                    message_batch: list[int] = []

                    async for message in channel.history(limit=None):
                        if deleted_count >= self.max_deletions:
                            break

                        if self.filter_engine.matches_rule(rule_name, message):
                            message_batch.append(message.id)
                            logger.info(
                                f"[BATCH] Added message {message.id} to batch "
                                f"(batch size: {len(message_batch)}/{self.batch_size}) "
                                f"from {message.author} in #{channel.name}: "
                                f"{message.content[:50]}"
                            )

                            if self.dry_run:
                                logger.info(
                                    f"[DRY RUN] Would delete message {message.id} "
                                    f"from {message.author} in #{channel.name}: "
                                    f"{message.content[:50]}"
                                )
                            else:
                                deleted_count += 1

                            if (
                                not self.dry_run
                                and len(message_batch) >= self.batch_size
                            ):
                                batch_to_delete = message_batch[: self.batch_size]
                                deleted = await self._bulk_delete_messages(
                                    channel, batch_to_delete
                                )
                                deleted_count += deleted
                                message_batch = message_batch[self.batch_size :]

                                await asyncio.sleep(self.api_call_interval)

                    if not self.dry_run and message_batch:
                        deleted = await self._bulk_delete_messages(
                            channel, message_batch
                        )
                        deleted_count += deleted
                        await asyncio.sleep(self.api_call_interval)

                    if self.dry_run:
                        deleted_count += len(message_batch)

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
